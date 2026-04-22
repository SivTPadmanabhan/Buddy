from dataclasses import dataclass
from typing import Any

from pinecone import Pinecone

from app.logging_config import get_logger
from app.services.usage import UsageTracker


log = get_logger(__name__)

PINECONE_USAGE_KEY = "pinecone_vectors"


class VectorLimitExceeded(Exception):
    pass


@dataclass
class ChunkRecord:
    id: str
    vector: list[float]
    metadata: dict[str, Any]


@dataclass
class SearchHit:
    id: str
    score: float
    metadata: dict[str, Any]


class VectorStore:
    def __init__(self, api_key: str, index_name: str, usage_tracker: UsageTracker):
        self._index_name = index_name
        self._usage = usage_tracker
        self._pc = Pinecone(api_key=api_key)
        self._index = self._pc.Index(index_name)

    def upsert_chunks(self, chunks: list[ChunkRecord]) -> None:
        if not chunks:
            return
        n = len(chunks)
        if not self._usage.check_limit(PINECONE_USAGE_KEY, n):
            log.warning(
                "pinecone_vector_limit_reached",
                category="system",
                action="limit_reached",
                service=PINECONE_USAGE_KEY,
                attempted=n,
            )
            raise VectorLimitExceeded(
                f"Upserting {n} vectors would exceed the pinecone_vectors limit"
            )

        vectors = [
            {"id": c.id, "values": c.vector, "metadata": c.metadata} for c in chunks
        ]
        self._index.upsert(vectors=vectors)
        self._usage.record_usage(PINECONE_USAGE_KEY, n)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[SearchHit]:
        result = self._index.query(
            vector=query_vector, top_k=top_k, include_metadata=True
        )
        matches = result.get("matches", []) if isinstance(result, dict) else result.matches
        hits: list[SearchHit] = []
        for m in matches:
            if isinstance(m, dict):
                hits.append(
                    SearchHit(
                        id=m["id"],
                        score=m["score"],
                        metadata=m.get("metadata", {}) or {},
                    )
                )
            else:
                hits.append(
                    SearchHit(
                        id=m.id,
                        score=m.score,
                        metadata=dict(m.metadata) if m.metadata else {},
                    )
                )
        return hits

    def delete_by_source(self, source_file: str) -> None:
        try:
            self._index.delete(filter={"source_file": {"$eq": source_file}})
        except Exception as e:
            if "Namespace not found" in str(e):
                return
            raise

    def get_vector_count(self) -> int:
        stats = self._index.describe_index_stats()
        if isinstance(stats, dict):
            return int(stats.get("total_vector_count", 0))
        return int(getattr(stats, "total_vector_count", 0))
