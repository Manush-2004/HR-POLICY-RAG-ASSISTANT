"""Unit tests for PDF document loading and metadata extraction."""

from pathlib import Path
import pypdf
import pytest
from langchain_core.documents import Document

from hr_assistant.document_loader import DocumentLoaderError, load_pdf

BASE_DIR = Path(__file__).resolve().parent.parent


def test_load_real_hr_policy_pdf():
    """Verify loading the real 208-page HR policy document."""
    real_pdf = BASE_DIR / "data" / "hr_policy.pdf"
    assert real_pdf.is_file(), "HR policy PDF must be present in backend/data/"

    documents = load_pdf(real_pdf)
    assert len(documents) > 100
    first_doc = documents[0]
    assert isinstance(first_doc, Document)
    assert first_doc.metadata["source"] == "hr_policy.pdf"
    assert "page" in first_doc.metadata
    assert "page_number" in first_doc.metadata
    assert first_doc.metadata["page_number"] == first_doc.metadata["page"] + 1
    assert len(first_doc.page_content) > 0


def test_load_pdf_missing_file(tmp_path):
    """Verify FileNotFoundError is raised when file does not exist."""
    missing_file = tmp_path / "nonexistent.pdf"
    with pytest.raises(FileNotFoundError, match="not found"):
        load_pdf(missing_file)


def test_load_pdf_empty_file(tmp_path):
    """Verify DocumentLoaderError is raised when file is 0 bytes."""
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")
    with pytest.raises(DocumentLoaderError, match="is empty"):
        load_pdf(empty_file)


def test_load_pdf_corrupted_file(tmp_path):
    """Verify DocumentLoaderError is raised when file contains corrupt data."""
    corrupt_file = tmp_path / "corrupt.pdf"
    corrupt_file.write_bytes(b"NOT A VALID PDF CONTENT AT ALL")
    with pytest.raises(DocumentLoaderError, match="Error parsing PDF file"):
        load_pdf(corrupt_file)


def test_load_pdf_blank_pages(tmp_path):
    """Verify DocumentLoaderError is raised when a PDF contains only blank pages."""
    blank_pdf = tmp_path / "all_blank.pdf"
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(blank_pdf, "wb") as f:
        writer.write(f)

    with pytest.raises(DocumentLoaderError, match="contains only blank pages"):
        load_pdf(blank_pdf)


def test_metadata_normalization():
    """Verify metadata keys: source, page, page_number on loaded document."""
    real_pdf = BASE_DIR / "data" / "hr_policy.pdf"
    docs = load_pdf(real_pdf)
    for doc in docs[:15]:
        assert doc.metadata["source"] == "hr_policy.pdf"
        assert isinstance(doc.metadata["page"], int)
        assert isinstance(doc.metadata["page_number"], int)
        assert doc.metadata["page_number"] == doc.metadata["page"] + 1
        assert doc.page_content.strip() != ""
