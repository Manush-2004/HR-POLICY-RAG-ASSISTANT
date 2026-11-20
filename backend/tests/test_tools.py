"""Unit tests for search_hr_policy LangChain tool."""

from unittest.mock import MagicMock
import pytest
from langchain_core.documents import Document

from hr_assistant.tools import (
    clear_retrieved_documents,
    create_search_tool,
    format_retrieved_chunks,
    get_last_retrieved_documents,
)


@pytest.fixture
def sample_chunks():
    """Sample Document chunks for testing retrieval formatting."""
    return [
        Document(
            page_content="Employees are eligible for 12 days of casual leave per calendar year.",
            metadata={"source": "hr_policy.pdf", "page": 14, "page_number": 15, "page_label": "15"},
        ),
        Document(
            page_content="Earned leave may be accumulated up to a maximum of 300 days.",
            metadata={"source": "hr_policy.pdf", "page": 16, "page_number": 17, "page_label": "17"},
        ),
    ]


def test_format_retrieved_chunks(sample_chunks):
    """Verify clean string formatting of retrieved chunks."""
    formatted = format_retrieved_chunks(sample_chunks)
    assert "Found 2 relevant policy excerpt(s):" in formatted
    assert "Document: hr_policy.pdf" in formatted
    assert "Page: 15" in formatted
    assert "Page: 17" in formatted
    assert "12 days of casual leave" in formatted
    assert "accumulated up to a maximum of 300 days" in formatted


def test_format_empty_chunks():
    """Verify output when no chunks are retrieved."""
    formatted = format_retrieved_chunks([])
    assert "No matching policy sections were found" in formatted


def test_create_search_tool_execution(sample_chunks):
    """Verify tool executes similarity search and tracks documents in context variable."""
    clear_retrieved_documents()
    assert get_last_retrieved_documents() == []

    mock_vector_store = MagicMock()
    mock_vector_store.similarity_search.return_value = sample_chunks

    search_tool = create_search_tool(vector_store=mock_vector_store, top_k=2)
    assert search_tool.name == "search_hr_policy"

    result_text = search_tool.invoke({"query": "leave entitlement"})
    assert mock_vector_store.similarity_search.call_count == 1
    mock_vector_store.similarity_search.assert_called_with("leave entitlement", k=2)

    assert "Found 2 relevant policy excerpt(s):" in result_text
    assert "Page: 15" in result_text

    # Verify context variable tracked the documents
    tracked = get_last_retrieved_documents()
    assert len(tracked) == 2
    assert tracked[0].page_content == sample_chunks[0].page_content

    clear_retrieved_documents()
    assert get_last_retrieved_documents() == []


def test_search_tool_handles_exception():
    """Verify tool gracefully formats errors when vector store fails."""
    mock_vector_store = MagicMock()
    mock_vector_store.similarity_search.side_effect = RuntimeError("Chroma connection error")

    search_tool = create_search_tool(vector_store=mock_vector_store)
    result = search_tool.invoke({"query": "error query"})

    assert "An error occurred while searching" in result
    assert "Chroma connection error" in result
