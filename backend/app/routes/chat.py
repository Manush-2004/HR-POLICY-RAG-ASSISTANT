"""Chat and health endpoints."""

import logging
from fastapi import APIRouter, status
from app.schemas.chat import HealthResponse
from hr_assistant.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["HR Assistant"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check and service status",
)
async def health_check() -> HealthResponse:
    """Verify backend availability, document presence, and configuration status."""
    settings = get_settings()
    policy_path = settings.resolve_hr_policy_path()
    store_path = settings.resolve_chroma_persist_directory()

    pdf_present = policy_path.is_file()
    vector_store_ready = store_path.is_dir() and any(store_path.iterdir()) if store_path.exists() else False
    llm_ready = bool(settings.effective_google_api_key)
    embeddings_ready = bool(settings.jina_api_key)

    service_status = "ok" if pdf_present else "degraded"

    return HealthResponse(
        status=service_status,
        version="0.1.0",
        policy_pdf_present=pdf_present,
        vector_store_initialized=vector_store_ready,
        llm_configured=llm_ready,
        embeddings_configured=embeddings_ready,
    )
