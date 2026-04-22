from functools import lru_cache

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.logging_config import get_logger
from app.services.embeddings import Embedder
from app.services.gemini import GeminiClient
from app.services.rag import GeminiLimitExceeded, RAGService
from app.services.vectorstore import VectorStore


log = get_logger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class SourceItem(BaseModel):
    source_file: str | None = None
    chunk_index: int | None = None
    score: float | None = None


class ChatResponse(BaseModel):
    response: str
    sources: list[SourceItem]


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
    return RAGService(
        embedder=embedder,
        vectorstore=vectorstore,
        gemini=gemini,
        usage_tracker=usage_tracker,
    )


def get_rag_service() -> RAGService:
    return _build_rag_service()


@router.post("/chat")
def chat(req: ChatRequest):
    svc = get_rag_service()
    try:
        result = svc.query(req.message)
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
