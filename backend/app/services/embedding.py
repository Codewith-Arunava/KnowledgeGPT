"""
Embedding Service — Multi-model embedding factory.
Supports: OpenAI small/large, Gemini, BGE-large, Sentence Transformers
"""
from typing import List
from functools import lru_cache
from langchain_core.embeddings import Embeddings
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_embedding_model(model_name: str | None = None) -> Embeddings:
    """
    Factory function — returns LangChain-compatible embedding model.
    model_name options: openai-small | openai-large | gemini | bge-large | sentence-transformers
    """
    model_name = model_name or settings.DEFAULT_EMBEDDING_MODEL
    logger.info("embedding.model.loading", model=model_name)

    if model_name == "openai-small":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.OPENAI_API_KEY,
        )

    elif model_name == "openai-large":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=settings.OPENAI_API_KEY,
        )

    elif model_name == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.GOOGLE_API_KEY,
        )

    elif model_name == "bge-large":
        from langchain_community.embeddings import HuggingFaceBgeEmbeddings
        return HuggingFaceBgeEmbeddings(
            model_name="BAAI/bge-large-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    elif model_name == "sentence-transformers":
        from langchain_community.embeddings import SentenceTransformerEmbeddings
        return SentenceTransformerEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )

    else:
        # Default fallback
        logger.warning("embedding.model.unknown", model=model_name, fallback="openai-small")
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.OPENAI_API_KEY,
        )


def get_llm(model_name: str | None = None, streaming: bool = False):
    """
    LLM factory — returns LangChain-compatible LLM.
    model_name options: gpt-4o | gpt-4.1 | gemini-2.5-pro | gemini-2.5-flash
    """
    model_name = model_name or settings.OPENAI_DEFAULT_MODEL
    logger.info("llm.loading", model=model_name)

    if model_name in ("gpt-4o", "gpt-4.1", "gpt-4o-mini"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            openai_api_key=settings.OPENAI_API_KEY,
            streaming=streaming,
            temperature=0.1,
        )

    elif model_name in ("gemini-2.5-pro", "gemini-2.5-flash", "gemini-pro"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GOOGLE_API_KEY,
            streaming=streaming,
            temperature=0.1,
        )

    else:
        # Fallback to GPT-4o
        logger.warning("llm.unknown_model", model=model_name, fallback="gpt-4o")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o",
            openai_api_key=settings.OPENAI_API_KEY,
            streaming=streaming,
            temperature=0.1,
        )
