import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app.logging_config import get_logger
from app.services.document import load_bytes, semantic_chunk
from app.services.drive import DriveService, FileMetadata
from app.services.embeddings import Embedder
from app.services.usage import UsageTracker
from app.services.vectorstore import ChunkRecord, VectorLimitExceeded, VectorStore

log = get_logger(__name__)


@dataclass
class SyncResult:
    files_processed: int = 0
    chunks_upserted: int = 0
    files_skipped: int = 0
    limit_reached: bool = False
    errors: list[str] = field(default_factory=list)


class SyncService:
    def __init__(
        self,
        drive: DriveService,
        embedder: Embedder,
        vectorstore: VectorStore,
        usage_tracker: UsageTracker,
        folder_ids: list[str],
        sync_state_path: str = "data/sync_state.json",
    ):
        self._drive = drive
        self._embedder = embedder
        self._vectorstore = vectorstore
        self._usage = usage_tracker
        self._folder_ids = folder_ids
        self._state_path = Path(sync_state_path)
        self._state = self._load_state()

    def _load_state(self) -> dict:
        if self._state_path.exists():
            return json.loads(self._state_path.read_text())
        return {"files": {}, "last_sync": None}

    def _save_state(self) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(json.dumps(self._state, indent=2))

    def _file_changed(self, meta: FileMetadata) -> bool:
        prev = self._state["files"].get(meta.id)
        if prev is None:
            return True
        if meta.md5 and prev.get("md5") != meta.md5:
            return True
        if not meta.md5 and prev.get("modified_time") != meta.modified_time:
            return True
        return False

    def run_sync(self) -> SyncResult:
        result = SyncResult()

        all_files: list[FileMetadata] = []
        for folder_id in self._folder_ids:
            try:
                files = self._drive.list_files(folder_id)
                all_files.extend(files)
            except Exception as e:
                log.warning(
                    "sync_list_failed",
                    category="sync",
                    action="list_files",
                    folder_id=folder_id,
                    error=str(e),
                )
                result.errors.append(f"list {folder_id}: {e}")

        for meta in all_files:
            if not self._file_changed(meta):
                result.files_skipped += 1
                continue

            try:
                content = self._drive.download_file(meta.id, meta.mime_type)
                text = load_bytes(content, meta.mime_type, meta.name)
                if not text.strip():
                    log.info(
                        "sync_empty_document",
                        category="sync",
                        action="parse_document",
                        file=meta.name,
                    )
                    result.files_skipped += 1
                    continue

                chunk_results = semantic_chunk(text, meta.mime_type, self._embedder)

                records = [
                    ChunkRecord(
                        id=f"{meta.id}::{cr.chunk_index}",
                        vector=cr.vector,
                        metadata={
                            "source_file": meta.name,
                            "file_id": meta.id,
                            "chunk_index": cr.chunk_index,
                            "text": cr.text[:500],
                        },
                    )
                    for cr in chunk_results
                ]

                self._vectorstore.delete_by_source(meta.name)
                self._vectorstore.upsert_chunks(records)

                result.files_processed += 1
                result.chunks_upserted += len(records)

                self._state["files"][meta.id] = {
                    "name": meta.name,
                    "md5": meta.md5,
                    "modified_time": meta.modified_time,
                    "synced_at": datetime.now(timezone.utc).isoformat(),
                }

            except VectorLimitExceeded:
                log.warning(
                    "sync_vector_limit_reached",
                    category="sync",
                    action="limit_reached",
                    file=meta.name,
                )
                result.limit_reached = True
                break

            except Exception as e:
                log.warning(
                    "sync_file_failed",
                    category="sync",
                    action="process_file",
                    file=meta.name,
                    error=str(e),
                )
                result.errors.append(f"{meta.name}: {e}")

        self._state["last_sync"] = datetime.now(timezone.utc).isoformat()
        self._save_state()

        log.info(
            "sync_complete",
            category="sync",
            action="sync_complete",
            files_processed=result.files_processed,
            chunks_upserted=result.chunks_upserted,
            files_skipped=result.files_skipped,
            limit_reached=result.limit_reached,
        )

        return result

    def get_status(self) -> dict:
        self._state = self._load_state()
        usage = self._usage.get_usage_status()
        return {
            "last_sync": self._state.get("last_sync"),
            "files_synced": len(self._state.get("files", {})),
            "vector_usage": usage.get("pinecone_vectors", {}),
        }
