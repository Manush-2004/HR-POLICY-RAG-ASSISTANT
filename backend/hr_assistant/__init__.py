"""HR Policy Assistant core package."""

from hr_assistant.agent import (
    SYSTEM_PROMPT,
    build_agent,
    build_gemini_llm,
    format_chat_history,
    run_agent,
)
from hr_assistant.config import Settings, get_settings
from hr_assistant.document_loader import DocumentLoaderError, load_pdf
from hr_assistant.embeddings import get_embeddings
from hr_assistant.pipeline import (
    HRAssistant,
    build_hr_assistant,
    get_hr_assistant,
    reset_hr_assistant,
)
from hr_assistant.splitter import split_documents
from hr_assistant.tools import (
    clear_retrieved_documents,
    create_search_tool,
    format_retrieved_chunks,
    get_last_retrieved_documents,
)
from hr_assistant.vector_store import (
    COLLECTION_NAME,
    compute_index_fingerprint,
    get_or_create_vector_store,
    is_index_valid,
)

__version__ = "0.1.0"

__all__ = [
    "COLLECTION_NAME",
    "DocumentLoaderError",
    "HRAssistant",
    "SYSTEM_PROMPT",
    "Settings",
    "build_agent",
    "build_gemini_llm",
    "build_hr_assistant",
    "clear_retrieved_documents",
    "compute_index_fingerprint",
    "create_search_tool",
    "format_chat_history",
    "format_retrieved_chunks",
    "get_embeddings",
    "get_hr_assistant",
    "get_last_retrieved_documents",
    "get_or_create_vector_store",
    "get_settings",
    "is_index_valid",
    "load_pdf",
    "reset_hr_assistant",
    "run_agent",
    "split_documents",
]
