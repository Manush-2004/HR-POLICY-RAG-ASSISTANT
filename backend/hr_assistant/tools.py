"""Retrieval tool for searching HR policy documents in ChromaDB."""

import logging
import threading
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.tools import BaseTool, tool

from hr_assistant.config import get_settings

logger = logging.getLogger(__name__)

# Thread-safe global storage for retrieved documents in current request
_retrieval_lock = threading.Lock()
_last_retrieved_documents: List[Document] = []


def get_last_retrieved_documents() -> List[Document]:
    """Retrieve a copy of the document chunks collected during the most recent retrieval."""
    with _retrieval_lock:
        return list(_last_retrieved_documents)


def record_retrieved_documents(docs: List[Document]) -> None:
    """Record retrieved documents into the global tracker."""
    with _retrieval_lock:
        _last_retrieved_documents.extend(docs)


def clear_retrieved_documents() -> None:
    """Clear the tracked document chunks."""
    with _retrieval_lock:
        _last_retrieved_documents.clear()


def format_retrieved_chunks(chunks: List[Document]) -> str:
    """Format document chunks into a clean, structured context string for the agent."""
    if not chunks:
        return "No matching policy sections were found in the HR manual for this query."

    parts: List[str] = [f"Found {len(chunks)} relevant policy excerpt(s):\n"]

    for idx, chunk in enumerate(chunks, start=1):
        metadata = chunk.metadata or {}
        source = metadata.get("source", "hr_policy.pdf")
        page_num = metadata.get("page_number", metadata.get("page", 0) + 1)
        page_label = metadata.get("page_label", str(page_num))

        header = f"--- Excerpt {idx} [Document: {source} | Page: {page_num} (Label: {page_label})] ---"
        content = chunk.page_content.strip()
        parts.append(f"{header}\n{content}\n")

    return "\n".join(parts)


def create_search_tool(
    vector_store: Chroma,
    top_k: Optional[int] = None,
    document_tracker: Optional[List[Document]] = None,
) -> BaseTool:
    """Create a LangChain tool bound to the specified Chroma vector store.

    Args:
        vector_store: Initialized Chroma vector store instance.
        top_k: Number of chunks to retrieve. Defaults to settings.top_k.
        document_tracker: Optional mutable list that will receive retrieved Document objects.

    Returns:
        Callable LangChain BaseTool named 'search_hr_policy'.
    """
    settings = get_settings()
    k = top_k if top_k is not None else settings.top_k

    @tool
    def search_hr_policy(query: str) -> str:
        """Search the official company HR Policy Manual for rules, benefits, leave, conduct, and procedures.

        Args:
            query: Specific search terms or question regarding HR policy.

        Returns:
            Relevant excerpts from the HR policy manual with source and page citations.
        """
        logger.info("Executing search_hr_policy tool with query: %r (top_k=%d)", query, k)
        try:
            results: List[Document] = vector_store.similarity_search(query, k=k)
        except Exception as exc:
            logger.error("Error performing similarity search: %s", exc)
            return f"An error occurred while searching the HR policy vector database: {exc}"

        # Track retrieved documents
        record_retrieved_documents(results)
        if document_tracker is not None:
            document_tracker.extend(results)

        logger.info("Retrieved %d document chunks from vector store.", len(results))
        return format_retrieved_chunks(results)

    return search_hr_policy
