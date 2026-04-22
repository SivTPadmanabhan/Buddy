import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat as chat_api
from app.config import settings
from app.logging_config import configure_logging, get_logger
from app.services.usage import UsageTracker
from app.services.vectorstore import VectorStore

configure_logging()
log = get_logger("app.main")

usage_tracker = UsageTracker(
    settings.usage_file_path,
    {
        "gemini_requests": settings.gemini_daily_requests,
        "gemini_tokens": settings.gemini_daily_tokens,
        "pinecone_vectors": settings.pinecone_max_vectors,
    },
)


def _auto_sync() -> None:
    try:
        from app.api.chat import get_sync_service
        svc = get_sync_service()
        result = svc.run_sync()
        log.info(
            "auto_sync_complete",
            category="sync",
            action="auto_sync",
            files_processed=result.files_processed,
            chunks_upserted=result.chunks_upserted,
        )
    except Exception as e:
        log.warning(
            "auto_sync_failed",
            category="sync",
            action="auto_sync",
            error=str(e),
        )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log.info("startup", category="system", action="startup")
    if settings.sync_on_startup:
        asyncio.get_event_loop().run_in_executor(None, _auto_sync)
    yield
    log.info("shutdown", category="system", action="shutdown")


app = FastAPI(
    title="Buddy API",
    description="RAG-powered personal knowledge assistant",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_api.router)


def _check_pinecone() -> dict:
    if not settings.pinecone_api_key:
        return {"status": "unconfigured"}
    try:
        vs = VectorStore(
            api_key=settings.pinecone_api_key,
            index_name=settings.pinecone_index_name,
            usage_tracker=usage_tracker,
        )
        count = vs.get_vector_count()
        return {"status": "ok", "total_vector_count": count}
    except Exception as e:
        log.warning(
            "pinecone_health_check_failed",
            category="system",
            action="health_check",
            error=str(e),
        )
        return {"status": "error", "error": str(e)}


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "usage": usage_tracker.get_usage_status(),
        "services": {
            "pinecone": _check_pinecone(),
            "gemini": "unchecked",
            "drive": "unchecked",
        },
    }
