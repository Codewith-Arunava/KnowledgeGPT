"""
Chat API — Streaming RAG with LangGraph multi-agent pipeline.
Handles new conversations, follow-ups, SSE streaming.
"""
import uuid
import time
import json
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.analytics import AnalyticsEvent, EventType
from app.schemas.chat import ChatRequest, ChatResponse, ConversationListResponse, ConversationResponse, MessageResponse
from app.api.deps import get_current_user
from app.agents.graph import run_agent_pipeline, AgentState

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = get_logger(__name__)


@router.post("/", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run the full agent pipeline and return the response."""
    start_time = time.time()

    # Verify KB ownership
    kb_result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == payload.knowledge_base_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )
    kb = kb_result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # Get or create conversation
    if payload.conversation_id:
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == payload.conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(
            user_id=current_user.id,
            knowledge_base_id=payload.knowledge_base_id,
            title=payload.message[:60] + ("..." if len(payload.message) > 60 else ""),
            model=payload.model,
        )
        db.add(conversation)
        await db.flush()

    # Load conversation history
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.timestamp.asc())
        .limit(20)
    )
    history = [
        {"role": m.role.value, "content": m.content}
        for m in history_result.scalars().all()
    ]

    # Build agent state
    initial_state: AgentState = {
        "query": payload.message,
        "knowledge_base_id": str(payload.knowledge_base_id),
        "conversation_id": str(conversation.id),
        "user_id": str(current_user.id),
        "model": payload.model,
        "search_type": payload.search_type,
        "top_k": payload.top_k,
        "deep_research": payload.deep_research,
        "retriever_type": payload.retriever_type or kb.retriever_type.value,
        "embedding_model": kb.embedding_model.value,
        "vector_store_type": kb.vector_store.value,
        "conversation_history": history,
        # Initialize all optional fields
        "query_intent": None, "query_type": None, "entities": None,
        "refined_query": None, "retrieval_strategy": None,
        "retrieved_chunks": None, "avg_retrieval_score": None, "retrieval_metadata": None,
        "research_notes": None, "research_findings": None, "information_gaps": None,
        "web_search_needed": False, "web_search_results": None,
        "summary": None, "summary_type": None,
        "verified_citations": None, "citation_confidence": None,
        "hallucination_risk": None, "hallucination_score": None, "unsupported_claims": None,
        "final_answer": None, "citations": None, "answer_confidence": None,
        "updated_history": None, "session_context": None,
        "feedback_stored": False,
        "agents_executed": [], "tokens_used": None, "response_time_ms": None, "errors": [],
    }

    # Run the agent pipeline
    result_state = await run_agent_pipeline(initial_state)

    response_time = (time.time() - start_time) * 1000

    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role=MessageRole.user,
        content=payload.message,
    )
    db.add(user_msg)

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conversation.id,
        role=MessageRole.assistant,
        content=result_state.get("final_answer", ""),
        model_used=payload.model,
        retrieval_score=result_state.get("avg_retrieval_score"),
        hallucination_score=result_state.get("hallucination_score"),
        citation_confidence=result_state.get("citation_confidence"),
        answer_confidence=result_state.get("answer_confidence"),
        response_time_ms=response_time,
        citations=result_state.get("citations"),
        agent_trace={
            "query_intent": result_state.get("query_intent"),
            "query_type": result_state.get("query_type"),
            "entities": result_state.get("entities"),
            "chunks_retrieved": len(result_state.get("retrieved_chunks") or []),
            "retrieval_scores": [
                c.get("score", 0) for c in (result_state.get("retrieved_chunks") or [])[:5]
            ],
            "hallucination_risk": result_state.get("hallucination_risk"),
            "hallucination_score": result_state.get("hallucination_score"),
            "citation_confidence": result_state.get("citation_confidence"),
            "answer_confidence": result_state.get("answer_confidence"),
            "research_notes": result_state.get("research_notes", "")[:500],
            "web_search_used": result_state.get("web_search_needed", False),
            "agents_executed": result_state.get("agents_executed", []),
        },
    )
    db.add(assistant_msg)

    # Log analytics
    db.add(AnalyticsEvent(
        user_id=current_user.id,
        event_type=EventType.deep_research if payload.deep_research else EventType.query,
        knowledge_base_id=payload.knowledge_base_id,
        response_time_ms=response_time,
        retrieval_score=result_state.get("avg_retrieval_score"),
        hallucination_score=result_state.get("hallucination_score"),
        model_used=payload.model,
    ))

    await db.flush()

    # Build citation response objects
    from app.schemas.chat import Citation
    citations = [
        Citation(
            document_name=c.get("document_name", "Unknown"),
            page_number=c.get("page_number", 1),
            chunk_id=c.get("chunk_id", ""),
            content_preview=c.get("content_preview", ""),
            similarity_score=float(c.get("similarity_score", 0.0)),
        )
        for c in (result_state.get("citations") or [])
    ]

    from app.schemas.chat import AgentTrace
    agent_trace = AgentTrace(
        query_intent=result_state.get("query_intent"),
        query_type=result_state.get("query_type"),
        entities=result_state.get("entities"),
        chunks_retrieved=len(result_state.get("retrieved_chunks") or []),
        retrieval_scores=[
            c.get("score", 0) for c in (result_state.get("retrieved_chunks") or [])[:5]
        ],
        hallucination_risk=result_state.get("hallucination_risk"),
        hallucination_score=result_state.get("hallucination_score"),
        citation_confidence=result_state.get("citation_confidence"),
        answer_confidence=result_state.get("answer_confidence"),
        research_notes=result_state.get("research_notes"),
        web_search_used=result_state.get("web_search_needed", False),
        agents_executed=result_state.get("agents_executed", []),
    )

    return ChatResponse(
        message_id=assistant_msg.id,
        conversation_id=conversation.id,
        answer=result_state.get("final_answer", ""),
        citations=citations,
        agent_trace=agent_trace,
        retrieval_score=result_state.get("avg_retrieval_score"),
        hallucination_score=result_state.get("hallucination_score"),
        tokens_used=result_state.get("tokens_used"),
        response_time_ms=response_time,
        model_used=payload.model,
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
    )
    conversations = result.scalars().all()
    return ConversationListResponse(
        conversations=[ConversationResponse.model_validate(c) for c in conversations],
        total=len(conversations),
    )


@router.get("/conversations/{conv_id}", response_model=ConversationResponse)
async def get_conversation(
    conv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Load messages
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.timestamp.asc())
    )
    conv.messages = msg_result.scalars().all()
    return ConversationResponse.model_validate(conv)


@router.delete("/conversations/{conv_id}", status_code=204)
async def delete_conversation(
    conv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)
