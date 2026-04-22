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


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log.info("startup", category="system", action="startup")
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
    allow_origins=["http://localhost:3000"],
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
