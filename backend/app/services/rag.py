from app.logging_config import get_logger
from app.services.embeddings import Embedder
from app.services.gemini import GeminiClient
from app.services.usage import UsageTracker
from app.services.vectorstore import VectorStore


log = get_logger(__name__)

PROMPT_TEMPLATE = """**Generate Response to User Query**
**Step 1: Parse Context Information**
Extract and utilize relevant knowledge from the provided context within `<context></context>` XML tags.
**Step 2: Analyze User Query**
Carefully read and comprehend the user's query, pinpointing the key concepts, entities, and intent behind the question.
**Step 3: Determine Response**
If the answer to the user's query can be directly inferred from the context information, provide a concise and accurate response in the same language as the user's query.
**Step 4: Handle Uncertainty**
If the answer is not clear, ask the user for clarification to ensure an accurate response.
**Step 5: Avoid Context Attribution**
When formulating your response, do not indicate that the information was derived from the context.
**Step 6: Respond in User's Language**
Maintain consistency by ensuring the response is in the same language as the user's query.
**Step 7: Provide Response**
Generate a clear, concise, and informative response to the user's query, adhering to the guidelines outlined above.
User Query: {query}
<context>
{context}
</context>
"""


class GeminiLimitExceeded(Exception):
    pass


class RAGService:
    def __init__(
        self,
        embedder: Embedder,
        vectorstore: VectorStore,
        gemini: GeminiClient,
        usage_tracker: UsageTracker,
        top_k: int = 5,
        warn_threshold: float = 0.8,
    ):
        self._embedder = embedder
        self._vectorstore = vectorstore
        self._gemini = gemini
        self._usage = usage_tracker
        self._top_k = top_k
        self._warn_threshold = warn_threshold

    def query(self, question: str) -> dict:
        if not self._usage.check_limit("gemini_requests", 1):
            log.warning(
                "gemini_request_limit_reached",
                category="system",
                action="limit_reached",
                service="gemini_requests",
            )
            raise GeminiLimitExceeded("gemini_requests daily limit reached")

        status = self._usage.get_usage_status()
        remaining_tokens = status["gemini_tokens"]["limit"] - status["gemini_tokens"]["used"]
        if remaining_tokens <= 0:
            log.warning(
                "gemini_token_limit_reached",
                category="system",
                action="limit_reached",
                service="gemini_tokens",
            )
            raise GeminiLimitExceeded("gemini_tokens daily limit reached")

        query_vec = self._embedder.embed_text(question)
        hits = self._vectorstore.search(query_vec, top_k=self._top_k)

        context = "\n\n".join(
            f"[{h.metadata.get('source_file', 'unknown')}] {h.metadata.get('text', '')}"
            for h in hits
        )
        prompt = PROMPT_TEMPLATE.format(query=question, context=context)

        text, input_tokens, output_tokens = self._gemini.generate(prompt)
        total_tokens = input_tokens + output_tokens

        self._usage.record_usage("gemini_requests", 1)
        self._usage.record_usage("gemini_tokens", total_tokens)

        self._maybe_warn_threshold()

        sources = [
            {
                "source_file": h.metadata.get("source_file"),
                "chunk_index": h.metadata.get("chunk_index"),
                "score": h.score,
            }
            for h in hits
        ]

        return {"response": text, "sources": sources}

    def _maybe_warn_threshold(self) -> None:
        status = self._usage.get_usage_status()
        for key in ("gemini_requests", "gemini_tokens"):
            pct = status[key]["percent"] / 100.0
            if pct >= self._warn_threshold:
                log.warning(
                    "gemini_usage_threshold",
                    category="system",
                    action="threshold_warning",
                    service=key,
                    percent=status[key]["percent"],
                )
