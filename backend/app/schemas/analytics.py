"""Pydantic schemas for Analytics, Evaluation, Feedback"""
import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


# ─── Analytics ──────────────────────────────────────────────────

class DailyStats(BaseModel):
    date: str
    queries: int
    uploads: int
    tokens_used: int
    avg_response_time_ms: float


class AnalyticsSummary(BaseModel):
    total_knowledge_bases: int
    total_documents: int
    total_conversations: int
    total_queries: int
    avg_retrieval_score: float
    avg_hallucination_score: float
    total_tokens_used: int
    estimated_cost_usd: float
    avg_response_time_ms: float
    daily_stats: List[DailyStats]
    top_documents: List[Dict[str, Any]]
    model_usage: Dict[str, int]


# ─── Evaluation ─────────────────────────────────────────────────

class ContextPrecisionResult(BaseModel):
    relevant_chunks: int
    total_retrieved: int
    precision_pct: float


class RetrievalAccuracyPoint(BaseModel):
    date: str
    accuracy: float


class HallucinationBreakdown(BaseModel):
    low: int
    medium: int
    high: int
    avg_score: float


class ConfidenceScores(BaseModel):
    retrieval_confidence: float
    citation_confidence: float
    answer_confidence: float


class EvaluationReport(BaseModel):
    context_precision: ContextPrecisionResult
    retrieval_accuracy_trend: List[RetrievalAccuracyPoint]
    hallucination_breakdown: HallucinationBreakdown
    confidence_scores: ConfidenceScores
    total_evaluated_queries: int


# ─── Feedback ────────────────────────────────────────────────────

class FeedbackCreate(BaseModel):
    message_id: uuid.UUID
    feedback_type: str  # like | dislike | rating | comment
    rating: Optional[int] = None  # 1-5
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    message_id: uuid.UUID
    feedback_type: str
    rating: Optional[int]
    comment: Optional[str]
    created_at: datetime
