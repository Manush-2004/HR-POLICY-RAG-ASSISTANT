"""Unit tests for FastAPI health and info endpoints."""

from fastapi import status


def test_root_endpoint(client):
    """Test the root service information endpoint."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "online"
    assert data["version"] == "0.1.0"
    assert "docs_url" in data
    assert "health_url" in data


def test_health_endpoint_healthy(client):
    """Test health endpoint when policy PDF and keys are present."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert data["policy_pdf_present"] is True
    assert data["llm_configured"] is True
    assert data["embeddings_configured"] is True


def test_health_endpoint_degraded(monkeypatch, tmp_path):
    """Test health endpoint when policy PDF is missing."""
    import hr_assistant.config as cfg
    from app.main import create_app
    from fastapi.testclient import TestClient

    missing_pdf = tmp_path / "nonexistent.pdf"
    monkeypatch.setenv("HR_POLICY_PATH", str(missing_pdf))
    cfg._settings = None

    app = create_app()
    with TestClient(app) as test_client:
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "degraded"
        assert data["policy_pdf_present"] is False
