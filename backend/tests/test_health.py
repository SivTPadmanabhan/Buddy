import pytest

from fastapi.testclient import TestClient

pytest.importorskip("sentence_transformers", reason="requires Docker environment")


def test_health_returns_ok(env, usage_file):
    from app.main import app
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "usage" in body
    assert "gemini_requests" in body["usage"]
    assert body["usage"]["gemini_requests"]["percent"] == 0.0
