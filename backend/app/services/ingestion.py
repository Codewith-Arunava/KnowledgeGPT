"""
PDF Ingestion Pipeline
Step 1: Load PDF → Step 2: Clean Text → Step 3: Chunk → Step 4: Embed → Step 5: Store
"""
import hashlib
import re
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LCDocument

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PDFIngestionPipeline:
    """Full PDF processing pipeline: load → clean → chunk → return."""

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    # ─── Step 1: Load ──────────────────────────────────────────
    def load_pdf(self, file_path: str) -> List[LCDocument]:
        """Load PDF pages using PyPDFLoader."""
        logger.info("ingestion.load_pdf.start", path=file_path)
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        logger.info("ingestion.load_pdf.done", pages=len(pages))
        return pages

    # ─── Step 2: Clean ─────────────────────────────────────────
    def clean_text(self, text: str) -> str:
        """Remove headers/footers, extra whitespace, empty lines."""
        # Remove lines that look like page numbers (short numeric lines)
        text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
        # Remove excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        # Remove common header/footer patterns
        text = re.sub(r"(?m)^(Page \d+|^\d+$|www\.\S+|http\S+)\s*$", "", text)
        # Strip leading/trailing whitespace per line
        lines = [line.strip() for line in text.split("\n")]
        # Remove very short lines that are likely noise
        lines = [line for line in lines if len(line) > 2 or line == ""]
        return "\n".join(lines).strip()

    # ─── Step 3: Chunk ─────────────────────────────────────────
    def chunk_documents(
        self,
        pages: List[LCDocument],
        document_id: str,
        document_name: str,
    ) -> List[LCDocument]:
        """Split pages into chunks with rich metadata."""
        cleaned_pages = []
        for page in pages:
            cleaned_content = self.clean_text(page.page_content)
            if cleaned_content:
                page.page_content = cleaned_content
                cleaned_pages.append(page)

        chunks = self.splitter.split_documents(cleaned_pages)

        # Enrich metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_id": f"{document_id}_chunk_{i}",
                "chunk_index": i,
                "document_id": document_id,
                "document_name": document_name,
                "page_number": chunk.metadata.get("page", 0) + 1,
                "chunk_size": len(chunk.page_content),
            })

        logger.info(
            "ingestion.chunk.done",
            document_id=document_id,
            total_chunks=len(chunks),
        )
        return chunks

    # ─── Full Pipeline ─────────────────────────────────────────
    def process(
        self,
        file_path: str,
        document_id: str,
        document_name: str,
    ) -> Dict[str, Any]:
        """Run the full pipeline and return chunks + metadata."""
        pages = self.load_pdf(file_path)
        chunks = self.chunk_documents(pages, document_id, document_name)
        return {
            "pages": len(pages),
            "chunks": len(chunks),
            "documents": chunks,
        }


def compute_file_hash(file_path: str) -> str:
    """SHA-256 hash for duplicate detection."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()


# Singleton pipeline
pipeline = PDFIngestionPipeline()
