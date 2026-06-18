"""PDF Ingestion pipeline unit tests."""
import pytest
import tempfile
import os
from pathlib import Path


def create_simple_pdf(path: str, text: str = "Hello World from PDF"):
    """Create a minimal valid PDF for testing."""
    import struct
    # Minimal PDF content
    content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {len(text) + 50} >>
stream
BT /F1 12 Tf 100 700 Td ({text}) Tj ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
trailer << /Size 6 /Root 1 0 R >>
startxref
0
%%EOF"""
    Path(path).write_text(content)


@pytest.mark.asyncio
async def test_pipeline_chunk_metadata():
    """Test that chunks have correct metadata."""
    from app.services.ingestion import PDFIngestionPipeline
    from langchain_core.documents import Document as LCDoc

    pipeline = PDFIngestionPipeline(chunk_size=200, chunk_overlap=20)
    pages = [
        LCDoc(page_content="This is test content. " * 20, metadata={"page": 0}),
        LCDoc(page_content="More content here. " * 20, metadata={"page": 1}),
    ]
    chunks = pipeline.chunk_documents(pages, "test-doc-id", "test.pdf")

    assert len(chunks) > 0
    for chunk in chunks:
        assert "chunk_id" in chunk.metadata
        assert "document_id" in chunk.metadata
        assert "document_name" in chunk.metadata
        assert chunk.metadata["document_name"] == "test.pdf"


@pytest.mark.asyncio
async def test_clean_text():
    """Test text cleaning removes noise."""
    from app.services.ingestion import PDFIngestionPipeline

    pipeline = PDFIngestionPipeline()
    dirty = "  Hello World  \n\n\n\nThis is content.\n123\n  \n  More content."
    clean = pipeline.clean_text(dirty)

    assert "Hello World" in clean
    assert "More content" in clean
    # Should not have 3+ consecutive newlines
    assert "\n\n\n" not in clean


@pytest.mark.asyncio
async def test_compute_file_hash():
    """Test SHA-256 hash computation for duplicate detection."""
    from app.services.ingestion import compute_file_hash
    import tempfile

    content = b"Test PDF content"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(content)
        f.flush()
        hash1 = compute_file_hash(f.name)
        hash2 = compute_file_hash(f.name)

    assert hash1 == hash2  # Same content = same hash
    assert len(hash1) == 64  # SHA-256 hex = 64 chars
    os.unlink(f.name)
