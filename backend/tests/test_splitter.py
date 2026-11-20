"""Unit tests for document splitting and chunking."""

import pytest
from langchain_core.documents import Document

from hr_assistant.splitter import split_documents


def test_split_documents_basic():
    """Verify basic splitting functionality."""
    docs = [
        Document(
            page_content="Section 1. " * 80,
            metadata={"source": "test.pdf", "page": 0, "page_number": 1},
        ),
        Document(
            page_content="Section 2. " * 80,
            metadata={"source": "test.pdf", "page": 1, "page_number": 2},
        ),
    ]

    chunks = split_documents(docs, chunk_size=200, chunk_overlap=40)
    assert len(chunks) > 2
    for chunk in chunks:
        assert len(chunk.page_content) <= 250
        assert chunk.metadata["source"] == "test.pdf"
        assert "page" in chunk.metadata
        assert "page_number" in chunk.metadata
        assert "chunk_id" in chunk.metadata


def test_split_documents_preserves_metadata():
    """Verify all original metadata keys are preserved in every chunk."""
    docs = [
        Document(
            page_content="Content paragraph one.\n\nContent paragraph two.\n\nContent paragraph three.",
            metadata={"source": "policy.pdf", "page": 5, "page_number": 6, "department": "HR"},
        )
    ]
    chunks = split_documents(docs, chunk_size=30, chunk_overlap=5)
    assert len(chunks) >= 3
    for chunk in chunks:
        assert chunk.metadata["source"] == "policy.pdf"
        assert chunk.metadata["page"] == 5
        assert chunk.metadata["page_number"] == 6
        assert chunk.metadata["department"] == "HR"


def test_split_empty_list():
    """Verify splitting empty list returns empty list without error."""
    assert split_documents([]) == []


def test_split_invalid_parameters():
    """Verify ValueError is raised for invalid chunk_size and chunk_overlap."""
    docs = [Document(page_content="Some test content", metadata={})]

    with pytest.raises(ValueError, match="chunk_size must be positive"):
        split_documents(docs, chunk_size=0, chunk_overlap=0)

    with pytest.raises(ValueError, match="chunk_size must be positive"):
        split_documents(docs, chunk_size=-100, chunk_overlap=0)

    with pytest.raises(ValueError, match="chunk_overlap cannot be negative"):
        split_documents(docs, chunk_size=100, chunk_overlap=-10)

    with pytest.raises(ValueError, match="strictly less than"):
        split_documents(docs, chunk_size=100, chunk_overlap=100)

    with pytest.raises(ValueError, match="strictly less than"):
        split_documents(docs, chunk_size=100, chunk_overlap=150)
