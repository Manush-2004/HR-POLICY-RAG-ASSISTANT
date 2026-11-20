"""FastAPI application entrypoint and lifespan management."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routes.chat import router as chat_router
from hr_assistant.config import get_settings
from hr_assistant.pipeline import build_hr_assistant

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("hr_assistant.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown resource handling."""
    settings = get_settings()
    logger.info("Initializing HR Policy Assistant API...")
    logger.info("HR Policy document at: %s", settings.resolve_hr_policy_path())

    app.state.settings = settings

    # Check prerequisites
    has_pdf = settings.resolve_hr_policy_path().is_file()
    has_google = bool(settings.effective_google_api_key)
    has_jina = bool(settings.jina_api_key)

    # Only pre-warm pipeline if not already injected (e.g., during tests)
    if getattr(app.state, "assistant", None) is None:
        if has_pdf and has_google and has_jina and "test-" not in (settings.jina_api_key or ""):
            try:
                logger.info("Pre-warming HRAssistant pipeline during application startup...")
                app.state.assistant = build_hr_assistant()
                logger.info("HRAssistant pipeline ready for requests.")
            except Exception as exc:
                logger.error("Failed to initialize HRAssistant on startup: %s", exc)
        else:
            logger.info("Deferred pipeline startup: test environment or missing live credentials.")

    yield

    logger.info("Shutting down HR Policy Assistant API.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="HR Policy RAG Assistant API",
        description="Production-quality RAG chatbot for employee HR policy queries.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS configuration
    origins = [
        settings.frontend_origin,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    unique_origins = list(dict.fromkeys(filter(None, origins)))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=unique_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Handle request validation errors cleanly
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning("Validation error on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exc.errors()},
        )

    # Centralized uncaught exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error processing request %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected server error occurred."},
        )

    # Root informational endpoint
    @app.get("/", tags=["Info"])
    async def root():
        return {
            "name": "HR Policy RAG Assistant API",
            "version": "0.1.0",
            "status": "online",
            "docs_url": "/docs",
            "health_url": "/health",
            "chat_url": "/api/chat",
        }

    # Register routes
    app.include_router(chat_router)

    return app


app = create_app()
