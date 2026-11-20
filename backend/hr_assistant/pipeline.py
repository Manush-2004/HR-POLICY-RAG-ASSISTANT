"""RAG pipeline module connecting ingestion, vector retrieval, and agent orchestration."""

import asyncio
import logging
from typing import Any, List, Optional

from langchain_chroma import Chroma
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from app.schemas.chat import ChatMessage, ChatResponse
from hr_assistant.agent import build_agent, build_gemini_llm, run_agent
from hr_assistant.config import get_settings
from hr_assistant.tools import create_search_tool
from hr_assistant.vector_store import get_or_create_vector_store

logger = logging.getLogger(__name__)


class HRAssistant:
    """Encapsulated HR Assistant RAG pipeline."""

    def __init__(
        self,
        vector_store: Chroma,
        llm: BaseChatModel,
        search_tool: BaseTool,
        agent: Any = None,
    ):
        self.vector_store = vector_store
        self.llm = llm
        self.search_tool = search_tool
        self.agent = agent or build_agent(
            llm=self.llm,
            tools=[self.search_tool],
            vector_store=self.vector_store,
        )

    def ask(
        self,
        question: str,
        history: Optional[List[ChatMessage]] = None,
    ) -> ChatResponse:
        """Process an employee question synchronously and return the grounded ChatResponse.

        Args:
            question: Employee question about HR policies.
            history: Optional conversational history.

        Returns:
            ChatResponse containing answer, citations, and policy_found flag.
        """
        cleaned_question = question.strip()
        if not cleaned_question:
            raise ValueError("Question cannot be empty or whitespace.")

        logger.info("Pipeline processing question: %r (history turns: %d)", cleaned_question, len(history or []))

        answer, sources, policy_found = run_agent(
            agent=self.agent,
            message=cleaned_question,
            history=history,
        )

        return ChatResponse(
            answer=answer,
            sources=sources,
            policy_found=policy_found,
        )

    async def aask(
        self,
        question: str,
        history: Optional[List[ChatMessage]] = None,
    ) -> ChatResponse:
        """Asynchronously process an employee question without blocking the event loop."""
        return await asyncio.to_thread(self.ask, question, history)


_assistant_instance: Optional[HRAssistant] = None


def build_hr_assistant(
    force_rebuild: bool = False,
    vector_store: Optional[Chroma] = None,
    llm: Optional[BaseChatModel] = None,
) -> HRAssistant:
    """Build or rebuild the unified HRAssistant pipeline singleton.

    Args:
        force_rebuild: Force rebuilding the vector store index.
        vector_store: Optional pre-configured Chroma vector store.
        llm: Optional pre-configured language model.

    Returns:
        Configured HRAssistant instance.
    """
    global _assistant_instance

    settings = get_settings()
    logger.info("Initializing HRAssistant pipeline (force_rebuild=%s)...", force_rebuild)

    vs = vector_store or get_or_create_vector_store(force_rebuild=force_rebuild)
    chat_llm = llm or build_gemini_llm()
    search_tool = create_search_tool(vector_store=vs, top_k=settings.top_k)

    agent = build_agent(
        llm=chat_llm,
        tools=[search_tool],
        vector_store=vs,
    )

    _assistant_instance = HRAssistant(
        vector_store=vs,
        llm=chat_llm,
        search_tool=search_tool,
        agent=agent,
    )

    logger.info("HRAssistant pipeline successfully built.")
    return _assistant_instance


def get_hr_assistant() -> HRAssistant:
    """Retrieve the active HRAssistant singleton, initializing if needed."""
    global _assistant_instance
    if _assistant_instance is None:
        _assistant_instance = build_hr_assistant()
    return _assistant_instance


def reset_hr_assistant() -> None:
    """Reset the singleton instance (used in tests)."""
    global _assistant_instance
    _assistant_instance = None


def ask(
    question: str,
    history: Optional[List[ChatMessage]] = None,
) -> ChatResponse:
    """Convenience functional interface to ask the HR assistant a question."""
    assistant = get_hr_assistant()
    return assistant.ask(question, history)
