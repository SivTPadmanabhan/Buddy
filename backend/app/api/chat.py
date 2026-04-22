from functools import lru_cache

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.logging_config import get_logger
from app.services.drive import DriveService
from app.services.embeddings import Embedder
from app.services.gemini import GeminiClient
from app.services.memory import MemoryService
from app.services.rag import GeminiLimitExceeded, RAGService
from app.services.sync import SyncService
from app.services.vectorstore import VectorStore


log = get_logger(__name__)

router = APIRouter()


class HistoryMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[HistoryMessage] | None = None


class SourceItem(BaseModel):
    source_file: str | None = None
    chunk_index: int | None = None
    score: float | None = None


class ChatResponse(BaseModel):
    response: str
    sources: list[SourceItem]


@lru_cache(maxsize=1)
def _build_memory_service() -> MemoryService:
    return MemoryService(
        api_key=settings.supermemory_api_key,
        container_tag=settings.supermemory_container_tag,
    )


@lru_cache(maxsize=1)
def _build_rag_service() -> RAGService:
    from app.main import usage_tracker

    embedder = Embedder()
    vectorstore = VectorStore(
        api_key=settings.pinecone_api_key,
        index_name=settings.pinecone_index_name,
        usage_tracker=usage_tracker,
    )
    gemini = GeminiClient(api_key=settings.gemini_api_key)
    memory = _build_memory_service()
    return RAGService(
        embedder=embedder,
        vectorstore=vectorstore,
        gemini=gemini,
        usage_tracker=usage_tracker,
        memory=memory,
    )


def get_rag_service() -> RAGService:
    return _build_rag_service()


@lru_cache(maxsize=1)
def _build_sync_service() -> SyncService:
    from app.main import usage_tracker

    drive = DriveService(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        token_path="data/drive_token.json",
    )
    embedder = Embedder()
    vectorstore = VectorStore(
        api_key=settings.pinecone_api_key,
        index_name=settings.pinecone_index_name,
        usage_tracker=usage_tracker,
    )
    return SyncService(
        drive=drive,
        embedder=embedder,
        vectorstore=vectorstore,
        usage_tracker=usage_tracker,
        folder_ids=settings.drive_folder_ids,
    )


def get_sync_service() -> SyncService:
    return _build_sync_service()


@router.post("/sync")
def sync():
    svc = get_sync_service()
    result = svc.run_sync()
    return {
        "files_processed": result.files_processed,
        "chunks_upserted": result.chunks_upserted,
        "files_skipped": result.files_skipped,
        "limit_reached": result.limit_reached,
        "errors": result.errors,
    }


@router.get("/sync/status")
def sync_status():
    svc = get_sync_service()
    return svc.get_status()


@router.post("/chat")
def chat(req: ChatRequest):
    svc = get_rag_service()
    history = [{"role": m.role, "content": m.content} for m in req.history] if req.history else None
    try:
        result = svc.query(req.message, history=history)
    except GeminiLimitExceeded as e:
        return JSONResponse(
            status_code=429,
            content={"error": str(e), "limit_reached": True},
        )
    return result


@router.get("/usage")
def usage():
    from app.main import usage_tracker
    return usage_tracker.get_usage_status()
