from unittest.mock import MagicMock, patch, call
import json

import pytest

from app.services.document import ChunkResult
from app.services.drive import FileMetadata
from app.services.sync import SyncService, SyncResult
from app.services.usage import UsageTracker
from app.services.vectorstore import VectorLimitExceeded


LIMITS = {
    "gemini_requests": 1000,
    "gemini_tokens": 500000,
    "pinecone_vectors": 100,
}

FAKE_CHUNK_RESULTS = [
    ChunkResult(text="chunk 0", vector=[0.1] * 384, chunk_index=0),
    ChunkResult(text="chunk 1", vector=[0.2] * 384, chunk_index=1),
]


@pytest.fixture
def tracker(tmp_path):
    return UsageTracker(tmp_path / "usage.json", LIMITS)


@pytest.fixture
def sync_state_path(tmp_path):
    return tmp_path / "sync_state.json"


@pytest.fixture
def drive():
    d = MagicMock()
    d.list_files.return_value = [
        FileMetadata(id="f1", name="doc1.pdf", mime_type="application/pdf",
                     modified_time="2026-04-20T10:00:00Z", md5="abc123"),
        FileMetadata(id="f2", name="notes.docx",
                     mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                     modified_time="2026-04-20T11:00:00Z", md5="def456"),
    ]
    d.download_file.return_value = b"fake content"
    return d


@pytest.fixture
def embedder():
    e = MagicMock()
    e.embed_batch.return_value = [[0.1] * 384, [0.2] * 384]
    return e


@pytest.fixture
def vectorstore():
    vs = MagicMock()
    vs.get_vector_count.return_value = 0
    return vs


@pytest.fixture
def svc(drive, embedder, vectorstore, tracker, sync_state_path):
    with patch("app.services.sync.load_bytes", return_value="Some parsed text that is long enough to chunk."), \
         patch("app.services.sync.semantic_chunk", return_value=FAKE_CHUNK_RESULTS):
        s = SyncService(
            drive=drive,
            embedder=embedder,
            vectorstore=vectorstore,
            usage_tracker=tracker,
            folder_ids=["folder_a"],
            sync_state_path=str(sync_state_path),
        )
        yield s


def test_full_sync_processes_all_files(svc, drive, embedder, vectorstore, sync_state_path):
    result = svc.run_sync()

    assert isinstance(result, SyncResult)
    assert result.files_processed == 2
    assert result.chunks_upserted >= 2
    assert drive.list_files.call_count == 1
    assert drive.download_file.call_count == 2
    assert vectorstore.upsert_chunks.call_count >= 1

    # State persisted
    state = json.loads(sync_state_path.read_text())
    assert "f1" in state["files"]
    assert "f2" in state["files"]


def test_incremental_sync_skips_unchanged(svc, drive, embedder, vectorstore, sync_state_path):
    # First sync
    svc.run_sync()

    # Second sync — same files, same md5
    drive.download_file.reset_mock()
    vectorstore.upsert_chunks.reset_mock()

    result = svc.run_sync()

    assert result.files_processed == 0
    assert result.files_skipped == 2
    drive.download_file.assert_not_called()


def test_incremental_sync_reprocesses_changed_file(svc, drive, embedder, vectorstore, sync_state_path):
    svc.run_sync()

    # Change md5 of one file
    drive.list_files.return_value = [
        FileMetadata(id="f1", name="doc1.pdf", mime_type="application/pdf",
                     modified_time="2026-04-21T10:00:00Z", md5="changed_hash"),
        FileMetadata(id="f2", name="notes.docx",
                     mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                     modified_time="2026-04-20T11:00:00Z", md5="def456"),
    ]
    drive.download_file.reset_mock()

    result = svc.run_sync()

    assert result.files_processed == 1
    assert result.files_skipped == 1
    drive.download_file.assert_called_once_with("f1", "application/pdf")


def test_sync_stops_at_vector_limit(drive, embedder, vectorstore, tracker, sync_state_path):
    for _ in range(10):
        tracker.record_usage("pinecone_vectors", 10)

    vectorstore.upsert_chunks.side_effect = VectorLimitExceeded("limit")

    with patch("app.services.sync.load_bytes", return_value="text"), \
         patch("app.services.sync.semantic_chunk", return_value=[
             ChunkResult(text="chunk 0", vector=[0.1] * 384, chunk_index=0),
         ]):
        svc = SyncService(
            drive=drive, embedder=embedder, vectorstore=vectorstore,
            usage_tracker=tracker, folder_ids=["folder_a"],
            sync_state_path=str(sync_state_path),
        )
        result = svc.run_sync()

    assert result.limit_reached is True


def test_sync_state_persists_across_instances(drive, embedder, vectorstore, tracker, sync_state_path):
    with patch("app.services.sync.load_bytes", return_value="text"), \
         patch("app.services.sync.semantic_chunk", return_value=[
             ChunkResult(text="chunk 0", vector=[0.1] * 384, chunk_index=0),
         ]):
        svc1 = SyncService(
            drive=drive, embedder=embedder, vectorstore=vectorstore,
            usage_tracker=tracker, folder_ids=["folder_a"],
            sync_state_path=str(sync_state_path),
        )
        svc1.run_sync()

        # New instance loads persisted state
        drive.download_file.reset_mock()
        svc2 = SyncService(
            drive=drive, embedder=embedder, vectorstore=vectorstore,
            usage_tracker=tracker, folder_ids=["folder_a"],
            sync_state_path=str(sync_state_path),
        )
        result = svc2.run_sync()

    assert result.files_skipped == 2
    drive.download_file.assert_not_called()
