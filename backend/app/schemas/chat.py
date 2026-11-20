"""Request and response schemas for chat and health endpoints."""

from typing import List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check status and dependency readiness."""

    status: str = Field(default="ok", description="Service status ('ok' or 'degraded')")
    version: str = Field(default="0.1.0", description="Application version")
    policy_pdf_present: bool = Field(..., description="Whether the HR policy PDF file exists")
    vector_store_initialized: bool = Field(
        default=False,
        description="Whether ChromaDB index is persisted and available",
    )
    llm_configured: bool = Field(
        default=False,
        description="Whether Gemini API key is configured",
    )
    embeddings_configured: bool = Field(
        default=False,
        description="Whether Jina API key is configured",
    )


class ChatMessage(BaseModel):
    """A single turn in conversational history."""

    role: str = Field(
        ...,
        pattern="^(user|assistant|system)$",
        description="Message author role",
    )
    content: str = Field(..., min_length=1, description="Message text content")


class SourceReference(BaseModel):
    """Grounding citation reference from policy document."""

    source: str = Field(..., description="Source document filename or identifier")
    page: Optional[int] = Field(default=None, description="Page number of the reference")
    snippet: str = Field(..., description="Relevant excerpt text from document")


class ChatRequest(BaseModel):
    """Chat request payload sent by the frontend client."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Employee question about HR policy",
    )
    history: List[ChatMessage] = Field(
        default_factory=list,
        description="Optional preceding conversation history",
    )


class ChatResponse(BaseModel):
    """Chat response payload returned to the frontend client."""

    answer: str = Field(..., description="Assistant answer grounded in HR policy")
    sources: List[SourceReference] = Field(
        default_factory=list,
        description="Document citations used to ground the answer",
    )
    policy_found: bool = Field(
        default=True,
        description="True if answered from policy, False if information was not found",
    )
