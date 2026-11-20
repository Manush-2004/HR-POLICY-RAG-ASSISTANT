"""HR Policy Assistant core package."""

from hr_assistant.config import Settings, get_settings
from hr_assistant.document_loader import DocumentLoaderError, load_pdf
from hr_assistant.splitter import split_documents

__version__ = "0.1.0"

__all__ = [
    "DocumentLoaderError",
    "Settings",
    "get_settings",
    "load_pdf",
    "split_documents",
]
