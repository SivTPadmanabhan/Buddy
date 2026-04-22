from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.services.sync import SyncResult


def test_post_sync_triggers_sync(env, usage_file):
    from app.main import app

    fake_result = SyncResult(
        files_processed=2, chunks_upserted=4, files_skipped=0, limit_reached=False, errors=[]
    )
    fake_svc = MagicMock()
    fake_svc.run_sync.return_value = fake_result

    with patch("app.api.chat.get_sync_service", return_value=fake_svc):
        client = TestClient(app)
        r = client.post("/sync")

    assert r.status_code == 200
    body = r.json()
    assert body["files_processed"] == 2
    assert body["chunks_upserted"] == 4
    assert body["limit_reached"] is False


def test_post_sync_reports_limit_reached(env, usage_file):
    from app.main import app

    fake_result = SyncResult(
        files_processed=1, chunks_upserted=2, files_skipped=1,
        limit_reached=True, errors=[]
    )
    fake_svc = MagicMock()
    fake_svc.run_sync.return_value = fake_result

    with patch("app.api.chat.get_sync_service", return_value=fake_svc):
        client = TestClient(app)
        r = client.post("/sync")

    assert r.status_code == 200
    body = r.json()
    assert body["limit_reached"] is True


def test_sync_status_returns_state(env, usage_file):
    from app.main import app

    fake_svc = MagicMock()
    fake_svc.get_status.return_value = {
        "last_sync": "2026-04-20T10:00:00Z",
        "files_synced": 5,
        "vector_usage": {"used": 100, "limit": 80000, "percent": 0.13},
    }

    with patch("app.api.chat.get_sync_service", return_value=fake_svc):
        client = TestClient(app)
        r = client.get("/sync/status")

    assert r.status_code == 200
    body = r.json()
    assert body["last_sync"] == "2026-04-20T10:00:00Z"
    assert body["files_synced"] == 5
    assert "vector_usage" in body
