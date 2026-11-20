"""FastAPI application entrypoint and lifespan management."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routes.chat import router as chat_router
from hr_assistant.config import get_settings

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
    logger.info("Checking HR Policy document at: %s", settings.resolve_hr_policy_path())

    if settings.resolve_hr_policy_path().is_file():
        logger.info("HR Policy PDF found.")
    else:
        logger.warning(
            "HR Policy PDF NOT found at %s. Please place hr_policy.pdf in data/",
            settings.resolve_hr_policy_path(),
        )

    if settings.effective_google_api_key:
        logger.info("Google Gemini API key configured.")
    else:
        logger.warning("GOOGLE_API_KEY is not set.")

    if settings.jina_api_key:
        logger.info("Jina API key configured.")
    else:
        logger.warning("JINA_API_KEY is not set.")

    # Storage for pipeline/assistant instances in future phases
    app.state.settings = settings

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
    ]
    # Remove duplicates while preserving order
    unique_origins = list(dict.fromkeys(origins))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=unique_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Centralized exception handler
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
        }

    # Register routers
    app.include_router(chat_router)

    return app


app = create_app()
