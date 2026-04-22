from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.services.rag import GeminiLimitExceeded


def test_chat_returns_response_and_sources(env, usage_file):
    from app.main import app

    fake_rag = MagicMock()
    fake_rag.query.return_value = {
        "response": "Paris.",
        "sources": [{"source_file": "file1.pdf", "chunk_index": 0, "score": 0.92}],
    }

    with patch("app.api.chat.get_rag_service", return_value=fake_rag):
        client = TestClient(app)
        r = client.post("/chat", json={"message": "What is the capital of France?"})

    assert r.status_code == 200
    body = r.json()
    assert body["response"] == "Paris."
    assert body["sources"][0]["source_file"] == "file1.pdf"


def test_chat_returns_429_when_limit_exceeded(env, usage_file):
    from app.main import app

    fake_rag = MagicMock()
    fake_rag.query.side_effect = GeminiLimitExceeded("gemini_requests limit reached")

    with patch("app.api.chat.get_rag_service", return_value=fake_rag):
        client = TestClient(app)
        r = client.post("/chat", json={"message": "hi"})

    assert r.status_code == 429
    body = r.json()
    assert body["limit_reached"] is True
    assert "error" in body


def test_usage_endpoint_returns_status(env, usage_file):
    from app.main import app
    client = TestClient(app)
    r = client.get("/usage")
    assert r.status_code == 200
    body = r.json()
    assert "gemini_requests" in body
    assert "gemini_tokens" in body
    assert "pinecone_vectors" in body
