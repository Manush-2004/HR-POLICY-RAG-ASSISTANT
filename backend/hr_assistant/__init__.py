"""HR Policy Assistant core package."""

from hr_assistant.config import Settings, get_settings
from hr_assistant.document_loader import DocumentLoaderError, load_pdf
from hr_assistant.embeddings import get_embeddings
from hr_assistant.splitter import split_documents
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
    "Settings",
    "compute_index_fingerprint",
    "get_embeddings",
    "get_or_create_vector_store",
    "get_settings",
    "is_index_valid",
    "load_pdf",
    "split_documents",
]
