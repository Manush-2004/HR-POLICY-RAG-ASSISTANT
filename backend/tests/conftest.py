"""Shared pytest fixtures and test configuration."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from hr_assistant.config import Settings, get_settings

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def test_settings(tmp_path, monkeypatch):
    """Fixture to ensure deterministic settings in tests."""
    real_pdf = BASE_DIR / "data" / "hr_policy.pdf"
    if real_pdf.is_file():
        pdf_path = real_pdf
    else:
        # Fallback if running in an isolated environment without real PDF
        pdf_path = tmp_path / "test_policy.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test")

    test_store = tmp_path / "store"
    test_store.mkdir(exist_ok=True)

    monkeypatch.setenv("HR_POLICY_PATH", str(pdf_path))
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
