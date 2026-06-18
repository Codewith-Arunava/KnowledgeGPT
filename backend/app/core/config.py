"""
KnowledgeGPT - Application Configuration
Reads all settings from environment variables with sensible defaults.
"""
from functools import lru_cache
from typing import List, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── App ──────────────────────────────────────────────────
    APP_NAME: str = "KnowledgeGPT"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-secret-key-in-production-32-chars-min"
    API_V1_PREFIX: str = "/api/v1"

    # ─── Database ─────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "knowledgegpt"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    DATABASE_URL: str = "sqlite+aiosqlite:///./knowledgegpt.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ─── JWT ──────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-this-jwt-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ─── OpenAI ───────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_DEFAULT_MODEL: str = "gpt-4o"
    OPENAI_DEFAULT_EMBEDDING: str = "text-embedding-3-small"

    # ─── Google Gemini ─────────────────────────────────────────
    GOOGLE_API_KEY: str = ""
    GEMINI_DEFAULT_MODEL: str = "gemini-2.5-flash"

    # ─── ChromaDB ─────────────────────────────────────────────
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_PERSIST_DIRECTORY: str = "./chromadb_data"

    # ─── Pinecone ─────────────────────────────────────────────
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = "us-east-1-aws"
    PINECONE_INDEX_NAME: str = "knowledgegpt"

    # ─── Vector Store ─────────────────────────────────────────
    DEFAULT_VECTOR_STORE: Literal["chromadb", "pinecone"] = "chromadb"

    # ─── Retriever ────────────────────────────────────────────
    DEFAULT_RETRIEVER: Literal["langchain", "llamaindex"] = "langchain"

    # ─── LangSmith ────────────────────────────────────────────
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "knowledgegpt"

    # ─── Web Search ───────────────────────────────────────────
    TAVILY_API_KEY: str = ""
    SERPER_API_KEY: str = ""

    # ─── File Upload ──────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = ["pdf"]

    # ─── CORS ─────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # ─── Rate Limiting ────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ─── Embedding ────────────────────────────────────────────
    DEFAULT_EMBEDDING_MODEL: Literal[
        "openai-small", "openai-large", "gemini", "bge-large", "sentence-transformers"
    ] = "openai-small"

    # ─── Chunking ─────────────────────────────────────────────
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # ─── Retrieval ────────────────────────────────────────────
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.7

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def has_openai(self) -> bool:
        return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY != "sk-your-openai-api-key-here")

    @property
    def has_gemini(self) -> bool:
        return bool(self.GOOGLE_API_KEY and self.GOOGLE_API_KEY != "your-google-api-key-here")

    @property
    def has_pinecone(self) -> bool:
        return bool(self.PINECONE_API_KEY and self.PINECONE_API_KEY != "your-pinecone-api-key-here")

    @property
    def has_tavily(self) -> bool:
        return bool(self.TAVILY_API_KEY and self.TAVILY_API_KEY != "your-tavily-api-key-here")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
