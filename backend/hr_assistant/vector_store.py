"""Persistent ChromaDB vector store management with fingerprint-based indexing."""

import hashlib
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from hr_assistant.config import get_settings
from hr_assistant.document_loader import load_pdf
from hr_assistant.embeddings import get_embeddings
from hr_assistant.splitter import split_documents

logger = logging.getLogger(__name__)

COLLECTION_NAME = "hr_policy_manual"
FINGERPRINT_FILE = ".fingerprint"
DEFAULT_BATCH_SIZE = 50


def compute_index_fingerprint(
    pdf_path: Path,
    chunk_size: int,
    chunk_overlap: int,
    embedding_model_name: str,
) -> str:
    """Compute a SHA-256 fingerprint representing the PDF content and chunking configuration.

    Args:
        pdf_path: Path to the source PDF file.
        chunk_size: Text splitter chunk size.
        chunk_overlap: Text splitter chunk overlap.
        embedding_model_name: Name of the embedding model.

    Returns:
        Hexadecimal SHA-256 hash string.
    """
    hasher = hashlib.sha256()

    with open(pdf_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)

    config_str = f"chunk_size={chunk_size}:chunk_overlap={chunk_overlap}:model={embedding_model_name}"
    hasher.update(config_str.encode("utf-8"))
    return hasher.hexdigest()


def read_stored_fingerprint(store_dir: Path) -> Optional[Dict[str, Any]]:
    """Read fingerprint metadata from the persistence directory if present."""
    fp_path = store_dir / FINGERPRINT_FILE
    if not fp_path.is_file():
        return None
    try:
        with open(fp_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Could not read fingerprint file at %s: %s", fp_path, exc)
        return None


def write_stored_fingerprint(
    store_dir: Path,
    fingerprint: str,
    pdf_path: Path,
    chunk_size: int,
    chunk_overlap: int,
    model_name: str,
    chunk_count: int,
) -> None:
    """Write fingerprint metadata to the persistence directory."""
    store_dir.mkdir(parents=True, exist_ok=True)
    fp_path = store_dir / FINGERPRINT_FILE
    payload = {
        "fingerprint": fingerprint,
        "source_pdf": pdf_path.name,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "embedding_model": model_name,
        "chunk_count": chunk_count,
        "indexed_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(fp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    logger.info("Saved index fingerprint metadata to: %s", fp_path)


def is_index_valid(
    store_dir: Path,
    expected_fingerprint: str,
    client: chromadb.PersistentClient,
    collection_name: str = COLLECTION_NAME,
) -> bool:
    """Verify if the persisted index exists, matches the expected fingerprint, and has items."""
    stored_data = read_stored_fingerprint(store_dir)
    if not stored_data or stored_data.get("fingerprint") != expected_fingerprint:
        return False

    try:
        existing_collections = [col.name for col in client.list_collections()]
        if collection_name not in existing_collections:
            return False
        col = client.get_collection(collection_name)
        count = col.count()
        return count > 0
    except Exception as exc:
        logger.warning("Error checking existing ChromaDB collection: %s", exc)
        return False


def get_or_create_vector_store(
    persist_directory: Optional[Union[str, Path]] = None,
    pdf_path: Optional[Union[str, Path]] = None,
    embedding_function: Optional[Embeddings] = None,
    force_rebuild: bool = False,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Chroma:
    """Get the existing ChromaDB vector store or build a new persistent index if needed.

    Args:
        persist_directory: Directory for ChromaDB persistence. Defaults to settings.
        pdf_path: Path to the HR policy PDF. Defaults to settings.
        embedding_function: LangChain Embeddings instance. Defaults to JinaEmbeddings.
        force_rebuild: If True, forces re-indexing regardless of fingerprint match.
        batch_size: Number of chunks per embedding ingestion batch.

    Returns:
        Configured Chroma vector store ready for similarity search and retrieval.
    """
    settings = get_settings()

    target_store_dir = (
        Path(persist_directory)
        if persist_directory is not None
        else settings.resolve_chroma_persist_directory()
    )
    target_pdf_path = (
        Path(pdf_path)
        if pdf_path is not None
        else settings.resolve_hr_policy_path()
    )

    if not target_pdf_path.is_file():
        raise FileNotFoundError(f"HR policy document not found at: {target_pdf_path}")

    # Use provided embeddings or instantiate Jina
    embeddings = embedding_function or get_embeddings()
    model_name = getattr(embeddings, "model_name", settings.jina_model)

    expected_fp = compute_index_fingerprint(
        pdf_path=target_pdf_path,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        embedding_model_name=model_name,
    )

    target_store_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(target_store_dir))

    # Check if existing index can be reused
    if not force_rebuild and is_index_valid(target_store_dir, expected_fp, client, COLLECTION_NAME):
        logger.info(
            "Existing vector store index at '%s' is up-to-date (fingerprint matches). "
            "Reusing persistent ChromaDB without re-embedding.",
            target_store_dir,
        )
        return Chroma(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
        )

    # Rebuild required
    logger.info(
        "Rebuilding persistent vector store at '%s' (force_rebuild=%s)...",
        target_store_dir,
        force_rebuild,
    )

    # Safely clear old collection if it exists
    existing_collections = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing_collections:
        logger.info("Deleting outdated collection '%s'...", COLLECTION_NAME)
        client.delete_collection(COLLECTION_NAME)

    # Ingest document and split
    documents = load_pdf(target_pdf_path)
    chunks = split_documents(
        documents,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    if not chunks:
        raise ValueError(f"No chunks generated from document '{target_pdf_path.name}'.")

    logger.info("Initializing fresh Chroma collection '%s'...", COLLECTION_NAME)
    vector_store = Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )

    # Ingest in controlled batches
    total_chunks = len(chunks)
    logger.info(
        "Embedding and inserting %d chunks into ChromaDB (batch_size=%d)...",
        total_chunks,
        batch_size,
    )

    for i in range(0, total_chunks, batch_size):
        batch = chunks[i : i + batch_size]
        vector_store.add_documents(batch)
        logger.info(
            "Ingested chunks %d to %d of %d (%.1f%%)",
            i + 1,
            min(i + batch_size, total_chunks),
            total_chunks,
            (min(i + batch_size, total_chunks) / total_chunks) * 100,
        )

    # Save new fingerprint metadata
    write_stored_fingerprint(
        store_dir=target_store_dir,
        fingerprint=expected_fp,
        pdf_path=target_pdf_path,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        model_name=model_name,
        chunk_count=total_chunks,
    )

    logger.info("Vector store build complete with %d chunks.", total_chunks)
    return vector_store
