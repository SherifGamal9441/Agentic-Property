"""Unit tests for memory node."""

import json
from unittest.mock import MagicMock, patch

from src.agents.state import AgentState
from src.nodes.memory import (
    memory_node,
    route_after_memory,
    _format_history_for_context,
)


def test_format_history_empty():
    """Empty history returns first-message placeholder."""
    result = _format_history_for_context([])
    assert "first message" in result.lower()


def test_format_history_with_messages():
    """History is formatted with role labels and truncated content."""
    history = [
        {"role": "user", "content": "2BR apartments in Dubai Marina"},
        {"role": "assistant", "content": "Found Marina Crest 2BR for AED 1.75M"},
    ]
    result = _format_history_for_context(history)
    assert "USER: 2BR apartments in Dubai Marina" in result
    assert "ASSISTANT: Found Marina Crest" in result


def test_format_history_truncates_long_messages():
    """Messages over 300 chars are truncated."""
    long_text = "x" * 500
    history = [{"role": "user", "content": long_text}]
    result = _format_history_for_context(history)
    assert "..." in result
    assert len(result.split(": ", 1)[1]) <= 303  # content + "...\n"


def test_format_history_capped_at_max_turns():
    """Only last N turns are included."""
    history = []
    for i in range(25):
        history.append({"role": "user", "content": f"question {i}"})
        history.append({"role": "assistant", "content": f"answer {i}"})
    result = _format_history_for_context(history)
    # Should contain recent messages but not the earliest ones
    assert "question 24" in result
    assert "answer 24" in result
    assert "question 0" not in result  # capped out


def test_empty_history_no_llm_call():
    """With empty history, no LLM is called, context shows first message."""
    state = AgentState(query="apartments in Dubai Marina", conversation_history=[])
    result = memory_node(state)
    assert "first message" in result["conversation_context"].lower()
    assert result.get("route") != "memory_direct"


def test_with_history_builds_context():
    """With history, context is built and previous queries appear."""
    state = AgentState(
        query="what about a 3BR instead?",
        conversation_history=[
            {"role": "user", "content": "2BR apartments in Dubai Marina"},
            {"role": "assistant", "content": "Found Marina Crest 2BR for AED 1.75M"},
        ],
    )
    result = memory_node(state)
    assert "Dubai Marina" in result["conversation_context"]
    assert "Marina Crest" in result["conversation_context"]


@patch("src.nodes.memory.get_llm")
def test_meta_question_detected(mock_llm):
    """Meta-question about conversation is detected and short-circuits."""
    mock_resp = MagicMock()
    mock_resp.content = json.dumps(
        {"is_meta": True, "reason": "asks about prior question"}
    )
    mock_llm.return_value.invoke.return_value = mock_resp

    state = AgentState(
        query="what was my last question?",
        conversation_history=[
            {"role": "user", "content": "2BR apartments in Dubai Marina"},
            {"role": "assistant", "content": "Found Marina Crest 2BR for AED 1.75M"},
        ],
    )
    result = memory_node(state)
    assert result["route"] == "memory_direct"


@patch("src.nodes.memory.get_llm")
def test_normal_followup_not_meta(mock_llm):
    """Follow-up property query with history is NOT classified as meta."""
    mock_resp = MagicMock()
    mock_resp.content = json.dumps(
        {"is_meta": False, "reason": "property follow-up"}
    )
    mock_llm.return_value.invoke.return_value = mock_resp

    state = AgentState(
        query="show me villas instead",
        conversation_history=[
            {"role": "user", "content": "2BR apartments in Dubai Marina"},
            {"role": "assistant", "content": "Found Marina Crest 2BR for AED 1.75M"},
        ],
    )
    result = memory_node(state)
    assert result.get("route") != "memory_direct"


@patch("src.nodes.memory.get_llm")
def test_unparseable_llm_response_defaults_to_non_meta(mock_llm):
    """When LLM returns garbage, we default to non-meta (safe fallback)."""
    mock_resp = MagicMock()
    mock_resp.content = "not valid json at all"
    mock_llm.return_value.invoke.return_value = mock_resp

    state = AgentState(
        query="what was my last question?",
        conversation_history=[
            {"role": "user", "content": "2BR apartments in Dubai Marina"},
            {"role": "assistant", "content": "Found Marina Crest"},
        ],
    )
    result = memory_node(state)
    assert result.get("route") != "memory_direct"


def test_route_after_memory():
    """Router returns correct target based on state."""
    state = AgentState(route="memory_direct")
    assert route_after_memory(state) == "answer_generation"

    state = AgentState(route=None)
    assert route_after_memory(state) == "query_relevancy"

    state = AgentState(route="query_routing")
    assert route_after_memory(state) == "query_relevancy"
