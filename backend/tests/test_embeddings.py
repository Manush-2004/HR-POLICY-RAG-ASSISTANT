"""Unit tests for Jina embeddings configuration and instantiation."""

import pytest
from langchain_community.embeddings import JinaEmbeddings

from hr_assistant.embeddings import get_embeddings


def test_get_embeddings_success():
    """Verify get_embeddings creates a valid JinaEmbeddings instance with valid key."""
    embeddings = get_embeddings(api_key="valid-test-key-123", model_name="jina-embeddings-v2-base-en")
    assert isinstance(embeddings, JinaEmbeddings)
    assert embeddings.model_name == "jina-embeddings-v2-base-en"


def test_get_embeddings_missing_key(monkeypatch):
    """Verify ValueError is raised when no API key is provided or configured."""
    monkeypatch.setenv("JINA_API_KEY", "")
    import hr_assistant.config as cfg
    cfg._settings = None

    with pytest.raises(ValueError, match="JINA_API_KEY is missing"):
        get_embeddings(api_key="")


def test_get_embeddings_placeholder_key():
    """Verify ValueError is raised when placeholder template key is used."""
    with pytest.raises(ValueError, match="JINA_API_KEY is missing"):
        get_embeddings(api_key="your-jina-api-key-here")
