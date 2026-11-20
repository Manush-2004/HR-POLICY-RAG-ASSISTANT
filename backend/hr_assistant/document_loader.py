"""Document loader module for extracting and normalizing PDF content."""

import logging
import warnings
from pathlib import Path
from typing import List, Optional, Union

from langchain_core.documents import Document

# Filter community sunset deprecation warning for cleaner logs
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from langchain_community.document_loaders import PyPDFLoader

from hr_assistant.config import get_settings

logger = logging.getLogger(__name__)


class DocumentLoaderError(Exception):
    """Raised when an error occurs during document loading or processing."""

    pass


def load_pdf(file_path: Optional[Union[str, Path]] = None) -> List[Document]:
    """Load a PDF document, extract text pages, and normalize metadata.

    Args:
        file_path: Path to the PDF file. If None, uses HR_POLICY_PATH from settings.

    Returns:
        List of LangChain Document objects with normalized metadata.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        DocumentLoaderError: If the file is empty, corrupted, or cannot be read.
    """
    settings = get_settings()

    if file_path is None:
        target_path = settings.resolve_hr_policy_path()
    else:
        target_path = Path(file_path)
        if not target_path.is_absolute():
            target_path = settings.resolve_hr_policy_path().parent / target_path

    logger.info("Attempting to load PDF document from: %s", target_path)

    if not target_path.exists():
        raise FileNotFoundError(f"HR policy document not found at: {target_path}")

    if not target_path.is_file():
        raise DocumentLoaderError(f"Specified path is not a file: {target_path}")

    file_size = target_path.stat().st_size
    if file_size == 0:
        raise DocumentLoaderError(f"HR policy PDF file is empty (0 bytes): {target_path}")

    try:
        loader = PyPDFLoader(str(target_path))
        raw_documents = loader.load()
    except Exception as exc:
        logger.error("Failed to load PDF file '%s': %s", target_path, exc)
        raise DocumentLoaderError(f"Error parsing PDF file '{target_path.name}': {exc}") from exc

    if not raw_documents:
        raise DocumentLoaderError(f"PDF loader returned no pages for: {target_path.name}")

    normalized_documents: List[Document] = []
    skipped_empty_pages = 0

    for idx, doc in enumerate(raw_documents):
        content = (doc.page_content or "").strip()
        if not content:
            skipped_empty_pages += 1
            continue

        raw_page = doc.metadata.get("page", idx)
        page_int = int(raw_page) if isinstance(raw_page, (int, float, str)) and str(raw_page).isdigit() else idx

        # Preserve and standardize critical metadata
        metadata = dict(doc.metadata)
        metadata["source"] = target_path.name  # Clean basename (e.g. hr_policy.pdf)
        metadata["full_path"] = str(target_path)
        metadata["page"] = page_int  # 0-indexed for LangChain standard
        metadata["page_number"] = page_int + 1  # 1-indexed for human citations
        if "page_label" not in metadata:
            metadata["page_label"] = str(page_int + 1)

        normalized_documents.append(
            Document(page_content=content, metadata=metadata)
        )

    logger.info(
        "Successfully loaded %d non-empty pages from '%s' (skipped %d empty pages).",
        len(normalized_documents),
        target_path.name,
        skipped_empty_pages,
    )

    if not normalized_documents:
        raise DocumentLoaderError(
            f"PDF file '{target_path.name}' contains only blank pages with no readable text."
        )

    return normalized_documents
