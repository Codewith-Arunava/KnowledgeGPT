"""Analytics, Evaluation, and Feedback API Routes"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.analytics import AnalyticsEvent, EventType
from app.models.feedback import Feedback, FeedbackType
from app.schemas.analytics import (
    AnalyticsSummary, DailyStats, EvaluationReport,
    FeedbackCreate, FeedbackResponse,
)
from app.api.deps import get_current_user
from app.services.evaluation import evaluation_service

analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])
evaluation_router = APIRouter(prefix="/evaluation", tags=["Evaluation"])
feedback_router = APIRouter(prefix="/feedback", tags=["Feedback"])


# ─── Analytics ──────────────────────────────────────────────────

@analytics_router.get("/", response_model=AnalyticsSummary)
async def get_analytics(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid
    uid = current_user.id
    if isinstance(uid, str):
        uid = uuid.UUID(uid)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Counts
    kb_count = (await db.execute(
        select(func.count(KnowledgeBase.id)).where(KnowledgeBase.user_id == uid)
    )).scalar() or 0

    doc_count = (await db.execute(
        select(func.count(Document.id))
        .join(KnowledgeBase, Document.knowledge_base_id == KnowledgeBase.id)
        .where(KnowledgeBase.user_id == uid)
    )).scalar() or 0

    conv_count = (await db.execute(
        select(func.count(Conversation.id)).where(Conversation.user_id == uid)
    )).scalar() or 0

    # Query events
    events_result = await db.execute(
        select(AnalyticsEvent).where(
            and_(AnalyticsEvent.user_id == uid, AnalyticsEvent.created_at >= since)
        )
    )
    events = events_result.scalars().all()
    query_events = [e for e in events if e.event_type == EventType.query]

    total_queries = len(query_events)
    avg_retrieval = (
        sum(e.retrieval_score for e in query_events if e.retrieval_score) / total_queries
        if total_queries else 0.0
    )
    avg_hallucination = (
        sum(e.hallucination_score for e in query_events if e.hallucination_score) / total_queries
        if total_queries else 0.0
    )
    total_tokens = sum(e.tokens_used or 0 for e in events)
    avg_response_time = (
        sum(e.response_time_ms or 0 for e in query_events) / total_queries
        if total_queries else 0.0
    )

    # Daily stats (last 30 days)
    from collections import defaultdict
    daily_map: dict = defaultdict(lambda: {"queries": 0, "uploads": 0, "tokens": 0, "times": []})
    for e in events:
        day = e.created_at.strftime("%Y-%m-%d")
        if e.event_type == EventType.query:
            daily_map[day]["queries"] += 1
            if e.response_time_ms:
                daily_map[day]["times"].append(e.response_time_ms)
        elif e.event_type == EventType.upload:
            daily_map[day]["uploads"] += 1
        if e.tokens_used:
            daily_map[day]["tokens"] += e.tokens_used

    daily_stats = [
        DailyStats(
            date=day,
            queries=v["queries"],
            uploads=v["uploads"],
            tokens_used=v["tokens"],
            avg_response_time_ms=sum(v["times"]) / len(v["times"]) if v["times"] else 0.0,
        )
        for day, v in sorted(daily_map.items())
    ]

    # Model usage
    model_usage: dict = defaultdict(int)
    for e in query_events:
        if e.model_used:
            model_usage[e.model_used] += 1

    # Estimated cost (rough GPT-4o pricing: $5/1M tokens)
    estimated_cost = (total_tokens / 1_000_000) * 5.0

    return AnalyticsSummary(
        total_knowledge_bases=kb_count,
        total_documents=doc_count,
        total_conversations=conv_count,
        total_queries=total_queries,
        avg_retrieval_score=round(avg_retrieval, 3),
        avg_hallucination_score=round(avg_hallucination, 3),
        total_tokens_used=total_tokens,
        estimated_cost_usd=round(estimated_cost, 4),
        avg_response_time_ms=round(avg_response_time, 1),
        daily_stats=daily_stats,
        top_documents=[],  # Extended in production
        model_usage=dict(model_usage),
    )


# ─── Evaluation ─────────────────────────────────────────────────

@evaluation_router.get("/", response_model=EvaluationReport)
async def get_evaluation(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid = str(current_user.id)

    context_precision = await evaluation_service.compute_context_precision(db, uid, days)
    hallucination_breakdown = await evaluation_service.compute_hallucination_breakdown(db, uid, days)
    confidence_scores = await evaluation_service.compute_confidence_scores(db, uid, days)
    accuracy_trend = await evaluation_service.get_retrieval_accuracy_trend(db, uid, days)

    # Total evaluated queries
    since = datetime.now(timezone.utc) - timedelta(days=days)
    import uuid
    uid_obj = current_user.id
    if isinstance(uid_obj, str):
        uid_obj = uuid.UUID(uid_obj)

    count = (await db.execute(
        select(func.count(AnalyticsEvent.id)).where(
            and_(
                AnalyticsEvent.user_id == uid_obj,
                AnalyticsEvent.event_type == EventType.query,
                AnalyticsEvent.created_at >= since,
            )
        )
    )).scalar() or 0

    from app.schemas.analytics import (
        ContextPrecisionResult, HallucinationBreakdown, ConfidenceScores,
        RetrievalAccuracyPoint
    )
    return EvaluationReport(
        context_precision=ContextPrecisionResult(**context_precision),
        retrieval_accuracy_trend=[RetrievalAccuracyPoint(**p) for p in accuracy_trend],
        hallucination_breakdown=HallucinationBreakdown(**hallucination_breakdown),
        confidence_scores=ConfidenceScores(**confidence_scores),
        total_evaluated_queries=count,
    )


# ─── Feedback ────────────────────────────────────────────────────

@feedback_router.post("/", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    payload: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate message exists
    msg_result = await db.execute(select(Message).where(Message.id == payload.message_id))
    if not msg_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Message not found")

    feedback = Feedback(
        message_id=payload.message_id,
        user_id=current_user.id,
        feedback_type=payload.feedback_type,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(feedback)
    await db.flush()
    return FeedbackResponse.model_validate(feedback)
