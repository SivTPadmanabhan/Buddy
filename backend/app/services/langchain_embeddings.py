from langchain_core.embeddings import Embeddings

from app.services.embeddings import Embedder


class LangChainEmbeddingsAdapter(Embeddings):
    def __init__(self, embedder: Embedder):
        self._embedder = embedder

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embedder.embed_batch(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embedder.embed_text(text)
