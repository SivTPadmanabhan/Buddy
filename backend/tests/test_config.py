import importlib

import pytest


def _fresh_settings():
    import app.config as config
    importlib.reload(config)
    return config.Settings(_env_file=None)


def test_settings_loads_required_env(env):
    s = _fresh_settings()
    assert s.google_client_id == "test-client-id"
    assert s.pinecone_api_key == "test-pinecone-key"
    assert s.gemini_api_key == "test-gemini-key"
    assert s.drive_folder_ids == ["folderA", "folderB"]


def test_settings_missing_required_raises(monkeypatch):
    for k in ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET",
              "PINECONE_API_KEY", "GEMINI_API_KEY", "DRIVE_FOLDER_IDS"]:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr("app.config.Settings.model_config",
                        {"env_file": None, "extra": "ignore"}, raising=False)
    from app.config import Settings
    with pytest.raises(Exception):
        Settings(_env_file=None)


def test_safety_limits_defaults(env):
    s = _fresh_settings()
    assert s.gemini_daily_requests == 1000
    assert s.gemini_daily_tokens == 500000
    assert s.pinecone_max_vectors == 80000


def test_pinecone_index_default(env):
    s = _fresh_settings()
    assert s.pinecone_index_name == "buddy-index"


def test_sync_on_startup_default(env):
    s = _fresh_settings()
    assert s.sync_on_startup is True
