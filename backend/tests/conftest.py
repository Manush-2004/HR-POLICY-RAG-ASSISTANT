"""Shared pytest fixtures and test configuration."""

import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from hr_assistant.config import Settings, get_settings


@pytest.fixture(autouse=True)
def test_settings(tmp_path, monkeypatch):
    """Fixture to ensure deterministic settings in tests."""
    test_pdf = tmp_path / "test_policy.pdf"
    test_pdf.write_bytes(b"%PDF-1.4 test header")

    test_store = tmp_path / "store"
    test_store.mkdir()

    monkeypatch.setenv("HR_POLICY_PATH", str(test_pdf))
    monkeypatch.setenv("CHROMA_PERSIST_DIRECTORY", str(test_store))
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("JINA_API_KEY", "test-jina-key")

    # Reset singleton
    import hr_assistant.config as cfg
    cfg._settings = None
    settings = get_settings()
    yield settings
    cfg._settings = None


@pytest.fixture
def client(test_settings):
    """FastAPI TestClient fixture."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
