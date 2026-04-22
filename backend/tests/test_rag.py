from unittest.mock import MagicMock

import pytest

from app.services.rag import RAGService, GeminiLimitExceeded
from app.services.usage import UsageTracker
from app.services.vectorstore import SearchHit


LIMITS = {
    "gemini_requests": 100,
    "gemini_tokens": 10000,
    "pinecone_vectors": 80000,
}


@pytest.fixture
def tracker(tmp_path):
    return UsageTracker(tmp_path / "usage.json", LIMITS)


@pytest.fixture
def embedder():
    e = MagicMock()
    e.embed_text.return_value = [0.1] * 384
    return e


@pytest.fixture
def vectorstore():
    vs = MagicMock()
    vs.search.return_value = [
        SearchHit(
            id="file1::0",
            score=0.92,
            metadata={"source_file": "file1.pdf", "chunk_index": 0, "text": "Paris is the capital of France."},
        ),
        SearchHit(
            id="file2::3",
            score=0.80,
            metadata={"source_file": "file2.docx", "chunk_index": 3, "text": "Other info."},
        ),
    ]
    return vs


@pytest.fixture
def gemini():
    g = MagicMock()
    g.generate.return_value = ("Paris.", 50, 5)
    return g


def test_query_returns_response_and_sources(embedder, vectorstore, gemini, tracker):
    svc = RAGService(embedder=embedder, vectorstore=vectorstore, gemini=gemini, usage_tracker=tracker)
    result = svc.query("What is the capital of France?")

    assert result["response"] == "Paris."
    assert len(result["sources"]) == 2
    assert result["sources"][0]["source_file"] == "file1.pdf"
    assert result["sources"][0]["score"] == 0.92

    embedder.embed_text.assert_called_once_with("What is the capital of France?")
    vectorstore.search.assert_called_once()


def test_query_uses_seven_step_prompt_template(embedder, vectorstore, gemini, tracker):
    svc = RAGService(embedder=embedder, vectorstore=vectorstore, gemini=gemini, usage_tracker=tracker)
    svc.query("What is the capital of France?")

    prompt = gemini.generate.call_args.args[0]
    assert "Step 1: Parse Context Information" in prompt
    assert "Step 7: Provide Response" in prompt
    assert "What is the capital of France?" in prompt
    assert "Paris is the capital of France." in prompt
    assert "<context>" in prompt and "</context>" in prompt


def test_query_records_token_usage(embedder, vectorstore, gemini, tracker):
    svc = RAGService(embedder=embedder, vectorstore=vectorstore, gemini=gemini, usage_tracker=tracker)
    svc.query("hi")

    status = tracker.get_usage_status()
    assert status["gemini_requests"]["used"] == 1
    assert status["gemini_tokens"]["used"] == 55


def test_query_blocked_when_request_limit_exceeded(embedder, vectorstore, gemini, tracker):
    for _ in range(100):
        tracker.record_usage("gemini_requests", 1)  # used = 100, at cap

    svc = RAGService(embedder=embedder, vectorstore=vectorstore, gemini=gemini, usage_tracker=tracker)
    with pytest.raises(GeminiLimitExceeded):
        svc.query("hi")

    gemini.generate.assert_not_called()


def test_query_blocked_when_token_limit_exceeded(embedder, vectorstore, gemini, tracker):
    tracker.record_usage("gemini_tokens", 10000)  # at cap

    svc = RAGService(embedder=embedder, vectorstore=vectorstore, gemini=gemini, usage_tracker=tracker)
    with pytest.raises(GeminiLimitExceeded):
        svc.query("hi")

    gemini.generate.assert_not_called()
