"""Knowledge Base model"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid as UUID
from app.core.database import Base
import enum


class VectorStoreType(str, enum.Enum):
    chromadb = "chromadb"
    pinecone = "pinecone"


class RetrieverType(str, enum.Enum):
    langchain = "langchain"
    llamaindex = "llamaindex"


class EmbeddingModel(str, enum.Enum):
    openai_small = "openai-small"
    openai_large = "openai-large"
    gemini = "gemini"
    bge_large = "bge-large"
    sentence_transformers = "sentence-transformers"


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    vector_store: Mapped[VectorStoreType] = mapped_column(
        SAEnum(VectorStoreType), default=VectorStoreType.chromadb
    )
    retriever_type: Mapped[RetrieverType] = mapped_column(
        SAEnum(RetrieverType), default=RetrieverType.langchain
    )
    embedding_model: Mapped[EmbeddingModel] = mapped_column(
        SAEnum(EmbeddingModel), default=EmbeddingModel.openai_small
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="knowledge_bases")  # noqa: F821
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        back_populates="knowledge_base", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(  # noqa: F821
        back_populates="knowledge_base", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeBase id={self.id} name={self.name}>"
