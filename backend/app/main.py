from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_config import configure_logging, get_logger
from app.services.usage import UsageTracker

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


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "usage": usage_tracker.get_usage_status(),
        "services": {
            "pinecone": "unchecked",
            "gemini": "unchecked",
            "drive": "unchecked",
        },
    }
