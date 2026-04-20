import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


REQUIRED_ENV = {
    "GOOGLE_CLIENT_ID": "test-client-id",
    "GOOGLE_CLIENT_SECRET": "test-client-secret",
    "PINECONE_API_KEY": "test-pinecone-key",
    "GEMINI_API_KEY": "test-gemini-key",
    "DRIVE_FOLDER_IDS": "folderA,folderB",
}


@pytest.fixture
def env(monkeypatch):
    for k, v in REQUIRED_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("SYNC_ON_STARTUP", raising=False)
    return monkeypatch


@pytest.fixture
def usage_file(tmp_path, monkeypatch):
    path = tmp_path / "usage.json"
    monkeypatch.setenv("USAGE_FILE_PATH", str(path))
    return path
