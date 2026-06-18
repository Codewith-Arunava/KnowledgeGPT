"""
KnowledgeGPT — FastAPI Application Entry Point
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.logging import setup_logging, get_logger

# ─── Logging ──────────────────────────────────────────────────
setup_logging()
logger = get_logger(__name__)

# ─── LangSmith ────────────────────────────────────────────────
if settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT

# ─── Rate Limiting ────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ─── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app.startup", env=settings.APP_ENV, debug=settings.DEBUG)
    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    # Initialize database tables
    await init_db()
    logger.info("app.ready")
    yield
    # Cleanup
    await close_db()
    logger.info("app.shutdown")


# ─── App ──────────────────────────────────────────────────────
app = FastAPI(
    title="KnowledgeGPT API",
    description="Production-grade Multi-Agent RAG Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ─── Rate Limiting ────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────
from app.api.auth import router as auth_router
from app.api.knowledge_base import router as kb_router
from app.api.documents import router as docs_router
from app.api.chat import router as chat_router
from app.api.analytics import analytics_router, evaluation_router, feedback_router

PREFIX = settings.API_V1_PREFIX

app.include_router(auth_router, prefix=PREFIX)
app.include_router(kb_router, prefix=PREFIX)
app.include_router(docs_router, prefix=PREFIX)
app.include_router(chat_router, prefix=PREFIX)
app.include_router(analytics_router, prefix=PREFIX)
app.include_router(evaluation_router, prefix=PREFIX)
app.include_router(feedback_router, prefix=PREFIX)


# ─── Health Check ─────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "env": settings.APP_ENV,
        "providers": {
            "openai": settings.has_openai,
            "gemini": settings.has_gemini,
            "pinecone": settings.has_pinecone,
            "tavily": settings.has_tavily,
        },
    }


@app.get("/", tags=["Health"])
async def root():
    return {"message": f"Welcome to {settings.APP_NAME} API", "docs": "/api/docs"}
