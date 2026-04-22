import threading

from app.logging_config import get_logger
from app.services.embeddings import Embedder
from app.services.gemini import GeminiClient
from app.services.memory import MemoryService
from app.services.usage import UsageTracker
from app.services.vectorstore import VectorStore


log = get_logger(__name__)

PROMPT_TEMPLATE = """You are Buddy, a personal knowledge assistant and study companion. Your goal is to help the user deeply understand their material, not just retrieve facts.

Guidelines:
- Explain concepts thoroughly with examples, analogies, and connections to related topics from the user's documents.
- Break down complex ideas step by step. Teach, don't just summarize.
- If you are less than 95% sure what the user is asking, ask a specific clarifying question before answering. For example: "Are you asking about X in the context of Y, or do you mean Z?"
- When the user's question is clear, answer fully and then suggest a follow-up question or related concept they might want to explore next.
- Draw connections between topics when relevant ("This relates to what your notes say about...").
- Answer naturally without mentioning that you are using documents or context.
- If the answer is not in the provided context, say so honestly and offer what you do know.
- Respond in the same language as the user's query.
{memory_section}
{history_section}
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
        memory: MemoryService | None = None,
        top_k: int = 5,
        warn_threshold: float = 0.8,
    ):
        self._embedder = embedder
        self._vectorstore = vectorstore
        self._gemini = gemini
        self._usage = usage_tracker
        self._memory = memory
        self._top_k = top_k
        self._warn_threshold = warn_threshold

    def query(
        self,
        question: str,
        history: list[dict] | None = None,
    ) -> dict:
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

        memory_context = ""
        if self._memory:
            memory_context = self._memory.get_memory_context(question)

        memory_section = ""
        if memory_context:
            memory_section = f"\n<memory>\n{memory_context}\n</memory>\n"

        history_section = ""
        if history:
            lines = []
            for msg in history[-10:]:
                role = msg.get("role", "user").capitalize()
                lines.append(f"{role}: {msg.get('content', '')}")
            history_section = (
                "\n<conversation_history>\n"
                + "\n".join(lines)
                + "\n</conversation_history>\n"
            )

        prompt = PROMPT_TEMPLATE.format(
            query=question,
            context=context,
            memory_section=memory_section,
            history_section=history_section,
        )

        text, input_tokens, output_tokens = self._gemini.generate(prompt)
        total_tokens = input_tokens + output_tokens

        self._usage.record_usage("gemini_requests", 1)
        self._usage.record_usage("gemini_tokens", total_tokens)

        self._maybe_warn_threshold()

        if self._memory:
            threading.Thread(
                target=self._memory.store_conversation,
                args=(question, text),
                daemon=True,
            ).start()

        sources = [
            {
                "source_file": h.metadata.get("source_file"),
                "chunk_index": h.metadata.get("chunk_index"),
                "score": h.score,
                "text_preview": (h.metadata.get("text", "") or "")[:300],
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
