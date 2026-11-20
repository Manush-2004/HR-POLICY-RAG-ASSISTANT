"""Unit tests for persistent ChromaDB storage, fingerprinting, and reuse."""

from pathlib import Path
from typing import List
from unittest.mock import MagicMock
import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from hr_assistant.vector_store import (
    COLLECTION_NAME,
    compute_index_fingerprint,
    get_or_create_vector_store,
    is_index_valid,
    read_stored_fingerprint,
)


class DeterministicMockEmbeddings(Embeddings):
    """Deterministic term-frequency based mock embeddings for fast, isolated unit tests."""

    def __init__(self, size: int = 128):
        self.size = size
        self.model_name = "test-mock-embeddings"

    def _embed_text(self, text: str) -> List[float]:
        vec = [0.0] * self.size
        for word in text.lower().split():
            idx = abs(hash(word)) % self.size
            vec[idx] += 1.0
        norm = sum(x**2 for x in vec) ** 0.5 or 1.0
        return [round(x / norm, 6) for x in vec]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_text(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_text(text)


@pytest.fixture
def mock_embeddings():
    """Deterministic mock embeddings fixture."""
    return DeterministicMockEmbeddings(size=128)


def test_compute_fingerprint_deterministic(tmp_path):
    """Verify that fingerprint is identical for same file and configuration."""
    test_pdf = tmp_path / "doc.pdf"
    test_pdf.write_bytes(b"%PDF-1.4 sample content for hash")

    fp1 = compute_index_fingerprint(test_pdf, 1000, 200, "jina-embeddings-v2-base-en")
    fp2 = compute_index_fingerprint(test_pdf, 1000, 200, "jina-embeddings-v2-base-en")
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256 length


def test_compute_fingerprint_changes_on_config_change(tmp_path):
    """Verify that fingerprint changes when chunk parameters change."""
    test_pdf = tmp_path / "doc.pdf"
    test_pdf.write_bytes(b"%PDF-1.4 sample content for hash")

    fp_base = compute_index_fingerprint(test_pdf, 1000, 200, "jina-embeddings-v2-base-en")
    fp_diff_chunk = compute_index_fingerprint(test_pdf, 500, 200, "jina-embeddings-v2-base-en")
    fp_diff_overlap = compute_index_fingerprint(test_pdf, 1000, 100, "jina-embeddings-v2-base-en")
    fp_diff_model = compute_index_fingerprint(test_pdf, 1000, 200, "other-model")

    assert fp_base != fp_diff_chunk
    assert fp_base != fp_diff_overlap
    assert fp_base != fp_diff_model


def test_vector_store_persistence_and_reuse(tmp_path, mock_embeddings, monkeypatch):
    """Verify vector store is created, persisted, and reused on second call without re-embedding."""
    store_dir = tmp_path / "store"
    pdf_path = Path(__file__).resolve().parent.parent / "data" / "hr_policy.pdf"

    # Mock load_pdf and split_documents to isolate vector store persistence logic
    sample_docs = [
        Document(
            page_content="Employee leave policy: Casual leave is 12 days per calendar year.",
            metadata={"source": "hr_policy.pdf", "page": 10, "page_number": 11},
        ),
        Document(
            page_content="Medical reimbursement policy covers hospitalization expenses up to Rs 500,000.",
            metadata={"source": "hr_policy.pdf", "page": 20, "page_number": 21},
        ),
    ]

    mock_load = MagicMock(return_value=sample_docs)
    mock_split = MagicMock(return_value=sample_docs)

    monkeypatch.setattr("hr_assistant.vector_store.load_pdf", mock_load)
    monkeypatch.setattr("hr_assistant.vector_store.split_documents", mock_split)

    # First call: creates store and indexes documents
    vs1 = get_or_create_vector_store(
        persist_directory=store_dir,
        pdf_path=pdf_path,
        embedding_function=mock_embeddings,
        force_rebuild=False,
    )
    assert mock_load.call_count == 1
    assert mock_split.call_count == 1

    # Verify fingerprint file was created
    stored_meta = read_stored_fingerprint(store_dir)
    assert stored_meta is not None
    assert "fingerprint" in stored_meta
    assert stored_meta["chunk_count"] == 2

    # Verify retrieval works on vs1
    results = vs1.similarity_search("Casual leave", k=1)
    assert len(results) == 1
    assert "Casual leave" in results[0].page_content
    assert results[0].metadata["page_number"] == 11

    # Reset mock counters
    mock_load.reset_mock()
    mock_split.reset_mock()

    # Second call: must REUSE existing store without calling load_pdf or split_documents!
    vs2 = get_or_create_vector_store(
        persist_directory=store_dir,
        pdf_path=pdf_path,
        embedding_function=mock_embeddings,
        force_rebuild=False,
    )
    assert mock_load.call_count == 0
    assert mock_split.call_count == 0

    # Verify retrieval works on reused store
    results2 = vs2.similarity_search("hospitalization", k=1)
    assert len(results2) == 1
    assert "hospitalization" in results2[0].page_content
    assert results2[0].metadata["page_number"] == 21


def test_vector_store_force_rebuild(tmp_path, mock_embeddings, monkeypatch):
    """Verify that force_rebuild=True forces re-indexing even if fingerprint matches."""
    store_dir = tmp_path / "store"
    pdf_path = Path(__file__).resolve().parent.parent / "data" / "hr_policy.pdf"

    sample_docs = [
        Document(
            page_content="Policy clause 101 on probation period.",
            metadata={"source": "hr_policy.pdf", "page": 5, "page_number": 6},
        )
    ]
    mock_load = MagicMock(return_value=sample_docs)
    mock_split = MagicMock(return_value=sample_docs)

    monkeypatch.setattr("hr_assistant.vector_store.load_pdf", mock_load)
    monkeypatch.setattr("hr_assistant.vector_store.split_documents", mock_split)

    # Initial creation
    get_or_create_vector_store(
        persist_directory=store_dir,
        pdf_path=pdf_path,
        embedding_function=mock_embeddings,
    )
    assert mock_load.call_count == 1

    # Force rebuild
    get_or_create_vector_store(
        persist_directory=store_dir,
        pdf_path=pdf_path,
        embedding_function=mock_embeddings,
        force_rebuild=True,
    )
    assert mock_load.call_count == 2
