"""Integration tests for FastAPI endpoints: chat, health, validation, and CORS."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas.chat import ChatResponse, SourceReference
from hr_assistant.pipeline import HRAssistant


@pytest.fixture
def mock_pipeline_app(test_settings, monkeypatch):
    """Create FastAPI test application with an attached mock HRAssistant."""
    app = create_app()

    mock_assistant = MagicMock(spec=HRAssistant)
    sample_response = ChatResponse(
        answer="According to hr_policy.pdf, Page 12, standard leave is 15 days.",
        sources=[
            SourceReference(
                source="hr_policy.pdf",
                page=12,
                snippet="Standard annual leave entitlement is 15 days.",
            )
        ],
        policy_found=True,
    )
    mock_assistant.aask = AsyncMock(return_value=sample_response)
    mock_assistant.ask = MagicMock(return_value=sample_response)

    app.state.assistant = mock_assistant
    return app


def test_chat_endpoint_success(mock_pipeline_app):
    """Verify POST /api/chat processes question and returns ChatResponse."""
    with TestClient(mock_pipeline_app) as client:
        payload = {
            "message": "What is the standard annual leave?",
            "history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hello! How can I help you?"},
            ],
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "policy_found" in data
        assert data["policy_found"] is True
        assert len(data["sources"]) == 1
        assert data["sources"][0]["page"] == 12
        assert "standard leave is 15 days" in data["answer"]


def test_chat_endpoint_empty_message_validation(mock_pipeline_app):
    """Verify validation error HTTP 422 for empty string message."""
    with TestClient(mock_pipeline_app) as client:
        response = client.post("/api/chat", json={"message": ""})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_chat_endpoint_missing_message(mock_pipeline_app):
    """Verify validation error HTTP 422 when message field is omitted."""
    with TestClient(mock_pipeline_app) as client:
        response = client.post("/api/chat", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_chat_endpoint_whitespace_message(mock_pipeline_app):
    """Verify HTTP 400 when message is solely whitespace."""
    mock_pipeline_app.state.assistant.aask.side_effect = ValueError(
        "Question cannot be empty or whitespace."
    )
    with TestClient(mock_pipeline_app) as client:
        response = client.post("/api/chat", json={"message": "   "})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot be empty" in response.json()["detail"]


def test_cors_headers(mock_pipeline_app):
    """Verify CORS middleware headers allow configured frontend origin."""
    with TestClient(mock_pipeline_app) as client:
        response = client.options(
            "/api/chat",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_health_endpoint_with_assistant(mock_pipeline_app):
    """Verify GET /health reports healthy status when assistant is active."""
    with TestClient(mock_pipeline_app) as client:
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert data["policy_pdf_present"] is True
        assert data["vector_store_initialized"] is True
