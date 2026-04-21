from unittest.mock import MagicMock, patch

import pytest

from app.services.usage import UsageTracker
from app.services.vectorstore import (
    ChunkRecord,
    SearchHit,
    VectorLimitExceeded,
    VectorStore,
)


LIMITS = {"gemini_requests": 1000, "gemini_tokens": 500000, "pinecone_vectors": 100}


@pytest.fixture
def tracker(tmp_path):
    return UsageTracker(tmp_path / "usage.json", LIMITS)


@pytest.fixture
def fake_index():
    idx = MagicMock()
    idx.describe_index_stats.return_value = {"total_vector_count": 0}
    return idx


@pytest.fixture
def store(tracker, fake_index):
    with patch("app.services.vectorstore.Pinecone") as pc_cls:
        pc_cls.return_value.Index.return_value = fake_index
        s = VectorStore(api_key="k", index_name="buddy", usage_tracker=tracker)
    return s


def _chunk(i: int) -> ChunkRecord:
    return ChunkRecord(
        id=f"file1::{i}",
        vector=[0.1] * 384,
        metadata={"source_file": "file1.pdf", "chunk_index": i, "text": f"chunk {i}"},
    )


def test_upsert_sends_to_pinecone(store, fake_index, tracker):
    store.upsert_chunks([_chunk(0), _chunk(1)])
    fake_index.upsert.assert_called_once()
    vectors_arg = fake_index.upsert.call_args.kwargs["vectors"]
    assert len(vectors_arg) == 2
    assert vectors_arg[0]["id"] == "file1::0"
    assert tracker.get_usage_status()["pinecone_vectors"]["used"] == 2


def test_upsert_blocked_when_limit_would_exceed(store, fake_index, tracker):
    # LIMITS["pinecone_vectors"] is 100
    for _ in range(10):
        tracker.record_usage("pinecone_vectors", 10)  # used = 100

    with pytest.raises(VectorLimitExceeded):
        store.upsert_chunks([_chunk(0)])

    fake_index.upsert.assert_not_called()


def test_search_returns_hits(store, fake_index):
    fake_index.query.return_value = {
        "matches": [
            {"id": "file1::3", "score": 0.91,
             "metadata": {"source_file": "file1.pdf", "chunk_index": 3, "text": "hi"}},
            {"id": "file2::0", "score": 0.80,
             "metadata": {"source_file": "file2.docx", "chunk_index": 0, "text": "yo"}},
        ]
    }
    hits = store.search([0.1] * 384, top_k=2)
    assert len(hits) == 2
    assert isinstance(hits[0], SearchHit)
    assert hits[0].id == "file1::3"
    assert hits[0].score == 0.91
    assert hits[0].metadata["source_file"] == "file1.pdf"
    fake_index.query.assert_called_once()
    kwargs = fake_index.query.call_args.kwargs
    assert kwargs["top_k"] == 2
    assert kwargs["include_metadata"] is True


def test_delete_by_source(store, fake_index):
    store.delete_by_source("file1.pdf")
    fake_index.delete.assert_called_once()
    kwargs = fake_index.delete.call_args.kwargs
    assert kwargs["filter"] == {"source_file": {"$eq": "file1.pdf"}}


def test_get_vector_count(store, fake_index):
    fake_index.describe_index_stats.return_value = {"total_vector_count": 42}
    assert store.get_vector_count() == 42
