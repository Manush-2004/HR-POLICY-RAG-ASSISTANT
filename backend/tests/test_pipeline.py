"""Unit tests for the HR Assistant RAG pipeline."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from langchain_core.documents import Document

from app.schemas.chat import ChatMessage, ChatResponse, SourceReference
from hr_assistant.pipeline import HRAssistant, build_hr_assistant, reset_hr_assistant


@pytest.fixture(autouse=True)
def clean_assistant():
    """Ensure pipeline singleton is reset between tests."""
    reset_hr_assistant()
    yield
    reset_hr_assistant()


@pytest.fixture
def mock_hr_assistant(monkeypatch):
    """Create an isolated HRAssistant instance with mocked components."""
    mock_vs = MagicMock()
    mock_llm = MagicMock()
    mock_tool = MagicMock()
    mock_agent = MagicMock()

    sample_sources = [
        SourceReference(source="hr_policy.pdf", page=10, snippet="Policy sample snippet")
    ]

    monkeypatch.setattr(
        "hr_assistant.pipeline.run_agent",
        MagicMock(return_value=("According to policy, probation is 1 year.", sample_sources, True)),
    )

    assistant = HRAssistant(
        vector_store=mock_vs,
        llm=mock_llm,
        search_tool=mock_tool,
        agent=mock_agent,
    )
    return assistant


def test_ask_successful(mock_hr_assistant):
    """Verify synchronous ask method returns populated ChatResponse."""
    response = mock_hr_assistant.ask("What is the probation period?")
    assert isinstance(response, ChatResponse)
    assert "probation is 1 year" in response.answer
    assert response.policy_found is True
    assert len(response.sources) == 1
    assert response.sources[0].page == 10


def test_ask_empty_question(mock_hr_assistant):
    """Verify ValueError is raised for blank or whitespace questions."""
    with pytest.raises(ValueError, match="Question cannot be empty"):
        mock_hr_assistant.ask("")

    with pytest.raises(ValueError, match="Question cannot be empty"):
        mock_hr_assistant.ask("   \n\t  ")


@pytest.mark.asyncio
async def test_aask_async(mock_hr_assistant):
    """Verify asynchronous aask method executes and returns ChatResponse."""
    history = [ChatMessage(role="user", content="Hi"), ChatMessage(role="assistant", content="Hello")]
    response = await mock_hr_assistant.aask("How long is probation?", history=history)
    assert isinstance(response, ChatResponse)
    assert response.policy_found is True
    assert len(response.sources) == 1


def test_build_hr_assistant_with_mocks(monkeypatch):
    """Verify build_hr_assistant constructs the pipeline with provided components."""
    mock_vs = MagicMock()
    mock_llm = MagicMock()
    mock_search_tool = MagicMock()
    mock_agent = MagicMock()

    monkeypatch.setattr("hr_assistant.pipeline.create_search_tool", MagicMock(return_value=mock_search_tool))
    monkeypatch.setattr("hr_assistant.pipeline.build_agent", MagicMock(return_value=mock_agent))

    assistant = build_hr_assistant(vector_store=mock_vs, llm=mock_llm)
    assert isinstance(assistant, HRAssistant)
    assert assistant.vector_store == mock_vs
    assert assistant.llm == mock_llm
