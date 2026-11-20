"""Document splitter module for chunking text with metadata preservation."""

import logging
from typing import List, Optional, Sequence

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from hr_assistant.config import get_settings

logger = logging.getLogger(__name__)


def split_documents(
    documents: Sequence[Document],
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> List[Document]:
    """Split documents into overlapping chunks while preserving metadata.

    Args:
        documents: Sequence of LangChain Document objects.
        chunk_size: Maximum chunk size in characters. Defaults to settings.chunk_size.
        chunk_overlap: Overlap between consecutive chunks. Defaults to settings.chunk_overlap.

    Returns:
        List of chunked Document objects with preserved and enriched metadata.

    Raises:
        ValueError: If chunk_size <= 0 or chunk_overlap is negative or >= chunk_size.
    """
    settings = get_settings()
    effective_chunk_size = chunk_size if chunk_size is not None else settings.chunk_size
    effective_chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.chunk_overlap

    if effective_chunk_size <= 0:
        raise ValueError(f"chunk_size must be positive, got {effective_chunk_size}")

    if effective_chunk_overlap < 0:
        raise ValueError(f"chunk_overlap cannot be negative, got {effective_chunk_overlap}")

    if effective_chunk_overlap >= effective_chunk_size:
        raise ValueError(
            f"chunk_overlap ({effective_chunk_overlap}) must be strictly less than "
            f"chunk_size ({effective_chunk_size})"
        )

    if not documents:
        logger.warning("Empty document sequence provided to split_documents.")
        return []

    logger.info(
        "Splitting %d documents (chunk_size=%d, chunk_overlap=%d)...",
        len(documents),
        effective_chunk_size,
        effective_chunk_overlap,
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=effective_chunk_size,
        chunk_overlap=effective_chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
        is_separator_regex=False,
    )

    raw_chunks = splitter.split_documents(list(documents))

    # Enrich chunks with tracking chunk_id and preserve metadata
    enriched_chunks: List[Document] = []
    for chunk_idx, chunk in enumerate(raw_chunks):
        metadata = dict(chunk.metadata)
        source = metadata.get("source", "document")
        page = metadata.get("page", 0)
        metadata["chunk_id"] = f"{source}_p{page}_c{chunk_idx}"

        enriched_chunks.append(
            Document(page_content=chunk.page_content, metadata=metadata)
        )

    logger.info("Successfully produced %d chunks from %d documents.", len(enriched_chunks), len(documents))
    return enriched_chunks
