"""Unit tests for Gemini agent configuration, prompt construction, and run logic."""

from unittest.mock import MagicMock
import pytest
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage

from app.schemas.chat import ChatMessage
from hr_assistant.agent import (
    build_gemini_llm,
    format_chat_history,
    run_agent,
)
from hr_assistant.tools import clear_retrieved_documents, record_retrieved_documents


def test_build_gemini_llm_missing_key(monkeypatch):
    """Verify ValueError is raised if GOOGLE_API_KEY is missing or empty."""
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    import hr_assistant.config as cfg
    cfg._settings = None

    with pytest.raises(ValueError, match="GOOGLE_API_KEY is missing"):
        build_gemini_llm(api_key="")


def test_build_gemini_llm_placeholder_key():
    """Verify ValueError is raised if placeholder template key is used."""
    with pytest.raises(ValueError, match="GOOGLE_API_KEY is missing"):
        build_gemini_llm(api_key="your-google-api-key-here")


def test_format_chat_history():
    """Verify conversion of ChatMessage schemas to LangChain messages."""
    history = [
        ChatMessage(role="user", content="What is the leave policy?"),
        ChatMessage(role="assistant", content="You have 12 casual leaves."),
    ]
    messages = format_chat_history(history)
    assert len(messages) == 2
    assert isinstance(messages[0], HumanMessage)
    assert messages[0].content == "What is the leave policy?"
    assert isinstance(messages[1], AIMessage)
    assert messages[1].content == "You have 12 casual leaves."


def test_format_chat_history_empty():
    """Verify empty history yields empty list."""
    assert format_chat_history([]) == []
    assert format_chat_history(None) == []


def test_run_agent_grounded_response():
    """Verify run_agent correctly parses answers, extracts sources, and sets policy_found=True."""
    sample_docs = [
        Document(
            page_content="Casual leave entitlement: 12 days annually.",
            metadata={"source": "hr_policy.pdf", "page": 14, "page_number": 15},
        )
    ]

    mock_agent = MagicMock()

    def mock_invoke_with_retrieval(*args, **kwargs):
        # Simulate tool execution populating retrieved documents
        record_retrieved_documents(sample_docs)
        return {
            "messages": [
                HumanMessage(content="What is casual leave?"),
                AIMessage(content="According to hr_policy.pdf, Page 15, casual leave is 12 days per year."),
            ]
        }

    mock_agent.invoke.side_effect = mock_invoke_with_retrieval

    answer, sources, policy_found = run_agent(
        agent=mock_agent,
        message="What is casual leave?",
    )

    assert "casual leave is 12 days per year" in answer
    assert policy_found is True
    assert len(sources) == 1
    assert sources[0].source == "hr_policy.pdf"
    assert sources[0].page == 15
    assert "Casual leave entitlement" in sources[0].snippet


def test_run_agent_out_of_policy_response():
    """Verify run_agent sets policy_found=False when answer states info not found."""
    sample_docs = [
        Document(
            page_content="Office security badge rules.",
            metadata={"source": "hr_policy.pdf", "page": 30, "page_number": 31},
        )
    ]

    mock_agent = MagicMock()

    def mock_invoke_not_found(*args, **kwargs):
        record_retrieved_documents(sample_docs)
        return {
            "messages": [
                HumanMessage(content="Can I bring my dog to work?"),
                AIMessage(content="I could not find information regarding bringing pets to work in the HR policy manual."),
            ]
        }

    mock_agent.invoke.side_effect = mock_invoke_not_found

    answer, sources, policy_found = run_agent(
        agent=mock_agent,
        message="Can I bring my dog to work?",
    )

    assert "could not find information" in answer
    assert policy_found is False


def test_run_agent_greeting_response():
    """Verify friendly greetings are acknowledged without demanding policy citations."""
    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {
        "messages": [
            HumanMessage(content="Hello!"),
            AIMessage(content="Hello! I am your HR Policy Assistant. How can I assist you with company policies today?"),
        ]
    }
    clear_retrieved_documents()

    answer, sources, policy_found = run_agent(
        agent=mock_agent,
        message="Hello!",
    )

    assert "Hello!" in answer
    assert len(sources) == 0
    assert policy_found is True
