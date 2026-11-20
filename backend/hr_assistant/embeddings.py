"""Embeddings configuration module for Jina AI embeddings."""

import logging
import warnings
from typing import Optional

from hr_assistant.config import get_settings

logger = logging.getLogger(__name__)

# Filter community sunset deprecation warning for clean logs
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from langchain_community.embeddings import JinaEmbeddings


def get_embeddings(
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> JinaEmbeddings:
    """Configure and instantiate JinaEmbeddings using the official integration.

    Args:
        api_key: Optional Jina API key. If not provided, reads from settings.
        model_name: Optional embedding model name. Defaults to settings.jina_model.

    Returns:
        Configured JinaEmbeddings instance.

    Raises:
        ValueError: If no valid Jina API key is found.
    """
    settings = get_settings()
    key = api_key or settings.jina_api_key
    model = model_name or settings.jina_model

    if not key or not key.strip() or "your-" in key:
        raise ValueError(
            "JINA_API_KEY is missing or unconfigured. Please provide a valid Jina AI API key "
            "in your backend/.env file or environment variables."
        )

    logger.info("Initializing JinaEmbeddings with model: %s", model)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        return JinaEmbeddings(
            jina_api_key=key.strip(),
            model_name=model,
        )
