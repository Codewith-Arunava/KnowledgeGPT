"""Pydantic schemas for Chat, Conversations, and Messages"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict


# ─── Chat ────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    knowledge_base_id: uuid.UUID
    message: str
    conversation_id: Optional[uuid.UUID] = None  # None = new conversation
    model: str = "gpt-4o"
    deep_research: bool = False
    retriever_type: Optional[str] = None  # override per-query
    search_type: Literal["similarity", "mmr", "hybrid"] = "similarity"
    top_k: int = 5


class Citation(BaseModel):
    document_name: str
    page_number: int
    chunk_id: str
    content_preview: str
    similarity_score: float


class AgentTrace(BaseModel):
    query_intent: Optional[str] = None
    query_type: Optional[str] = None
    entities: Optional[List[str]] = None
    chunks_retrieved: Optional[int] = None
    retrieval_scores: Optional[List[float]] = None
    hallucination_risk: Optional[str] = None
    hallucination_score: Optional[float] = None
    citation_confidence: Optional[float] = None
    answer_confidence: Optional[float] = None
    research_notes: Optional[str] = None
    web_search_used: bool = False
    agents_executed: Optional[List[str]] = None


class ChatResponse(BaseModel):
    message_id: uuid.UUID
    conversation_id: uuid.UUID
    answer: str
    citations: List[Citation] = []
    agent_trace: Optional[AgentTrace] = None
    retrieval_score: Optional[float] = None
    hallucination_score: Optional[float] = None
    tokens_used: Optional[int] = None
    response_time_ms: Optional[float] = None
    model_used: str


# ─── Conversations ───────────────────────────────────────────────

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    model_used: Optional[str]
    retrieval_score: Optional[float]
    hallucination_score: Optional[float]
    citation_confidence: Optional[float]
    answer_confidence: Optional[float]
    tokens_used: Optional[int]
    response_time_ms: Optional[float]
    citations: Optional[List[Dict[str, Any]]]
    agent_trace: Optional[Dict[str, Any]]
    timestamp: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    knowledge_base_id: uuid.UUID
    title: str
    model: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int
