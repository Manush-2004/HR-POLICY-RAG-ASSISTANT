"""Chat and health endpoints."""

import logging
from typing import Any
from fastapi import APIRouter, HTTPException, Request, status

from app.schemas.chat import ChatRequest, ChatResponse, HealthResponse
from hr_assistant.config import get_settings
from hr_assistant.pipeline import get_hr_assistant

logger = logging.getLogger(__name__)
router = APIRouter(tags=["HR Assistant"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check and service status",
)
@router.get(
    "/api/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def health_check(request: Request) -> HealthResponse:
    """Verify backend availability, document presence, and configuration status."""
    settings = get_settings()
    policy_path = settings.resolve_hr_policy_path()
    store_path = settings.resolve_chroma_persist_directory()

    pdf_present = policy_path.is_file()
    vector_store_ready = (
        store_path.is_dir() and any(store_path.iterdir())
        if store_path.exists()
        else False
    )
    llm_ready = bool(settings.effective_google_api_key)
    embeddings_ready = bool(settings.jina_api_key)

    # Check if assistant is attached to app state or ready
    assistant_ready = getattr(request.app.state, "assistant", None) is not None

    service_status = "ok" if (pdf_present and llm_ready and embeddings_ready) else "degraded"

    return HealthResponse(
        status=service_status,
        version="0.1.0",
        policy_pdf_present=pdf_present,
        vector_store_initialized=vector_store_ready or assistant_ready,
        llm_configured=llm_ready,
        embeddings_configured=embeddings_ready,
    )


@router.post(
    "/api/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question about HR policies",
)
async def chat_endpoint(payload: ChatRequest, request: Request) -> ChatResponse:
    """Accept an employee's question and conversation history, invoke RAG pipeline, and return answer with citations."""
    cleaned_query = payload.message.strip()
    if not cleaned_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty or whitespace.",
        )

    logger.info("Received chat request: %r", cleaned_query)

    # Obtain assistant instance from application lifespan state, falling back to singleton
    assistant = getattr(request.app.state, "assistant", None)
    if assistant is None:
        try:
            assistant = get_hr_assistant()
        except Exception as exc:
            logger.error("Failed to initialize HR assistant pipeline: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"HR Assistant pipeline is not ready: {exc}",
            ) from exc

    try:
        response: ChatResponse = await assistant.aask(
            question=payload.message,
            history=payload.history,
        )
        return response
    except ValueError as val_err:
        logger.warning("Invalid input for chat: %s", val_err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        logger.exception("Error processing chat question %r: %s", payload.message, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the policy answer. Please try again.",
        ) from exc
