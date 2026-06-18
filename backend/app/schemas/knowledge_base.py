"""Pydantic schemas for Knowledge Base & Documents"""
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.knowledge_base import VectorStoreType, RetrieverType, EmbeddingModel
from app.models.document import DocumentStatus


# ─── Knowledge Base ─────────────────────────────────────────────

class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    vector_store: VectorStoreType = VectorStoreType.chromadb
    retriever_type: RetrieverType = RetrieverType.langchain
    embedding_model: EmbeddingModel = EmbeddingModel.openai_small


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    vector_store: Optional[VectorStoreType] = None
    retriever_type: Optional[RetrieverType] = None
    embedding_model: Optional[EmbeddingModel] = None


class KnowledgeBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    vector_store: VectorStoreType
    retriever_type: RetrieverType
    embedding_model: EmbeddingModel
    created_at: datetime
    updated_at: datetime
    document_count: Optional[int] = 0


# ─── Document ────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    knowledge_base_id: uuid.UUID
    filename: str
    original_filename: str
    file_size: Optional[int]
    pages: Optional[int]
    chunks: Optional[int]
    status: DocumentStatus
    error_message: Optional[str]
    uploaded_at: datetime
    processed_at: Optional[datetime]


class DocumentUploadResponse(BaseModel):
    message: str
    documents: List[DocumentResponse]


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
