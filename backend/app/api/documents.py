"""
Documents API — Upload PDFs, list, delete with background ingestion.
"""
import uuid
import shutil
from pathlib import Path
from typing import List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, AsyncSessionLocal
from app.core.config import settings
from app.core.logging import get_logger
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.analytics import AnalyticsEvent, EventType
from app.schemas.knowledge_base import DocumentResponse, DocumentUploadResponse, DocumentListResponse
from app.api.deps import get_current_user
from app.services.ingestion import pipeline, compute_file_hash
from app.services.vector_store import get_vector_store

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = get_logger(__name__)


@router.post("/upload/{kb_id}", response_model=DocumentUploadResponse, status_code=201)
async def upload_documents(
    kb_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload one or more PDFs to a knowledge base."""
    # Verify KB ownership
    kb_result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id, KnowledgeBase.user_id == current_user.id
        )
    )
    kb = kb_result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    upload_dir = Path(settings.UPLOAD_DIR) / str(kb_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    created_docs = []
    for file in files:
        # Validate file type
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"{file.filename}: only PDF files allowed")

        # Validate file size
        content = await file.read()
        if len(content) > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename}: exceeds {settings.MAX_FILE_SIZE_MB}MB limit",
            )

        # Compute hash for duplicate detection
        import hashlib
        content_hash = hashlib.sha256(content).hexdigest()
        existing = await db.execute(
            select(Document).where(
                Document.knowledge_base_id == kb_id,
                Document.content_hash == content_hash,
            )
        )
        if existing.scalar_one_or_none():
            logger.info("document.duplicate_skipped", filename=file.filename)
            continue

        # Save file
        safe_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = upload_dir / safe_name
        file_path.write_bytes(content)

        doc = Document(
            knowledge_base_id=kb_id,
            filename=safe_name,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=len(content),
            status=DocumentStatus.pending,
            content_hash=content_hash,
            chroma_collection=f"kb_{str(kb_id).replace('-', '_')}",
        )
        db.add(doc)
        db.add(AnalyticsEvent(user_id=current_user.id, event_type=EventType.upload))
        await db.flush()
        created_docs.append(doc)

        # Schedule background ingestion
        background_tasks.add_task(
            ingest_document_background,
            doc_id=str(doc.id),
            file_path=str(file_path),
            doc_name=file.filename,
            collection_name=doc.chroma_collection,
            embedding_model=kb.embedding_model.value,
            vector_store_type=kb.vector_store.value,
        )

    return DocumentUploadResponse(
        message=f"Uploaded {len(created_docs)} document(s). Processing in background.",
        documents=[DocumentResponse.model_validate(d) for d in created_docs],
    )


@router.get("/{kb_id}", response_model=DocumentListResponse)
async def list_documents(
    kb_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify KB ownership
    kb_result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id, KnowledgeBase.user_id == current_user.id
        )
    )
    if not kb_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    result = await db.execute(
        select(Document)
        .where(Document.knowledge_base_id == kb_id)
        .order_by(Document.uploaded_at.desc())
    )
    docs = result.scalars().all()
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in docs],
        total=len(docs),
    )


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify ownership via KB
    kb_result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == doc.knowledge_base_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )
    if not kb_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized")

    # Delete physical file
    try:
        Path(doc.file_path).unlink(missing_ok=True)
    except Exception:
        pass

    await db.delete(doc)


# ─── Background Ingestion ──────────────────────────────────────

async def ingest_document_background(
    doc_id: str,
    file_path: str,
    doc_name: str,
    collection_name: str,
    embedding_model: str,
    vector_store_type: str,
):
    """Background task to process PDF and store embeddings."""
    async with AsyncSessionLocal() as db:
        try:
            # Update status to processing
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if not doc:
                return

            doc.status = DocumentStatus.processing
            await db.commit()

            # Run ingestion pipeline
            result = pipeline.process(file_path, doc_id, doc_name)

            # Store in vector store
            store = get_vector_store(vector_store_type, embedding_model)
            store.add_documents(result["documents"], collection_name)

            # Update doc record
            doc.pages = result["pages"]
            doc.chunks = result["chunks"]
            doc.status = DocumentStatus.ready
            doc.processed_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(
                "ingestion.complete",
                doc_id=doc_id,
                pages=result["pages"],
                chunks=result["chunks"],
            )
        except Exception as e:
            logger.error("ingestion.failed", doc_id=doc_id, error=str(e))
            async with AsyncSessionLocal() as err_db:
                result = await err_db.execute(select(Document).where(Document.id == doc_id))
                doc = result.scalar_one_or_none()
                if doc:
                    doc.status = DocumentStatus.failed
                    doc.error_message = str(e)[:1000]
                    await err_db.commit()
