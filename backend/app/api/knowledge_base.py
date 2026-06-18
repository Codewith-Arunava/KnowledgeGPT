"""
Knowledge Base API Routes — CRUD operations
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.models.analytics import AnalyticsEvent, EventType
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Bases"])


@router.post("/", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    kb = KnowledgeBase(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        vector_store=payload.vector_store,
        retriever_type=payload.retriever_type,
        embedding_model=payload.embedding_model,
    )
    db.add(kb)
    db.add(AnalyticsEvent(user_id=current_user.id, event_type=EventType.kb_create))
    await db.flush()

    return _kb_to_response(kb, 0)


@router.get("/", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.user_id == current_user.id)
    )
    kbs = result.scalars().all()

    # Get document counts
    count_result = await db.execute(
        select(Document.knowledge_base_id, func.count(Document.id))
        .where(Document.knowledge_base_id.in_([kb.id for kb in kbs]))
        .group_by(Document.knowledge_base_id)
    )
    counts = {row[0]: row[1] for row in count_result.fetchall()}

    return [_kb_to_response(kb, counts.get(kb.id, 0)) for kb in kbs]


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    kb = await _get_kb_or_404(db, kb_id, current_user.id)
    count = await _get_doc_count(db, kb_id)
    return _kb_to_response(kb, count)


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: uuid.UUID,
    payload: KnowledgeBaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    kb = await _get_kb_or_404(db, kb_id, current_user.id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(kb, field, value)
    await db.flush()
    count = await _get_doc_count(db, kb_id)
    return _kb_to_response(kb, count)


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(
    kb_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    kb = await _get_kb_or_404(db, kb_id, current_user.id)

    # Delete vector store collection
    try:
        from app.services.vector_store import get_vector_store
        store = get_vector_store(kb.vector_store.value)
        collection_name = f"kb_{str(kb_id).replace('-', '_')}"
        store.delete_collection(collection_name)
    except Exception:
        pass  # Don't fail if collection doesn't exist

    db.add(AnalyticsEvent(user_id=current_user.id, event_type=EventType.kb_delete))
    await db.delete(kb)


# ─── Helpers ──────────────────────────────────────────────────

async def _get_kb_or_404(db: AsyncSession, kb_id: uuid.UUID, user_id) -> KnowledgeBase:
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == user_id,
        )
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


async def _get_doc_count(db: AsyncSession, kb_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count(Document.id)).where(Document.knowledge_base_id == kb_id)
    )
    return result.scalar() or 0


def _kb_to_response(kb: KnowledgeBase, doc_count: int) -> KnowledgeBaseResponse:
    return KnowledgeBaseResponse(
        id=kb.id,
        user_id=kb.user_id,
        name=kb.name,
        description=kb.description,
        vector_store=kb.vector_store,
        retriever_type=kb.retriever_type,
        embedding_model=kb.embedding_model,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
        document_count=doc_count,
    )
