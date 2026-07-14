"""Unit tests for memory node."""

import json
from unittest.mock import MagicMock, patch

from src.agents.state import AgentState
from src.nodes.memory import (
    memory_node,
    route_after_memory,
    _format_history_for_context,
    _parse_llm_response,
)

# ── _format_history_for_context ───────────────────────────────────────────────

def test_format_history_empty():
    result = _format_history_for_context([])
    assert "first message" in result.lower()


def test_format_history_with_messages():
    history = [
        {"role": "user", "content": "2BR apartments in Dubai Marina"},
        {"role": "assistant", "content": "Found Marina Crest 2BR for AED 1.75M"},
    ]
    result = _format_history_for_context(history)
    assert "USER: 2BR apartments in Dubai Marina" in result
    assert "ASSISTANT: Found Marina Crest" in result


def test_format_history_truncates_long_messages():
    long_text = "x" * 500
    history = [{"role": "user", "content": long_text}]
    result = _format_history_for_context(history)
    assert "..." in result
    assert len(result.split(": ", 1)[1]) <= 303


def test_format_history_capped_at_max_turns():
    history = []
    for i in range(25):
        history.append({"role": "user", "content": f"question {i}"})
        history.append({"role": "assistant", "content": f"answer {i}"})
    result = _format_history_for_context(history)
    assert "question 24" in result
    assert "answer 24" in result
    assert "question 0" not in result


# ── _parse_llm_response ──────────────────────────────────────────────────────

def test_parse_clean_json():
    result = _parse_llm_response('{"category": "greeting", "reason": "user says hi"}')
    assert result["category"] == "greeting"


def test_parse_garbage_defaults_to_property():
    result = _parse_llm_response("not json at all")
    assert result["category"] == "general_query"


def test_parse_json_with_markdown_fence():
    result = _parse_llm_response('```json\n{"category": "meta_question"}\n```')
    assert result["category"] == "meta_question"


# ── memory_node (mocked LLM) ─────────────────────────────────────────────────

def _make_llm_mock(category: str = "property_query", reason: str = "test"):
    """Helper: create a mock LLM that returns a given category."""
    mock_resp = MagicMock()
    mock_resp.content = json.dumps({"category": category, "reason": reason})
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_resp
    return mock_llm


@patch("src.nodes.memory.get_llm")
def test_empty_history_classified_as_property(mock_get_llm):
    """Empty history with property query → classified as property_query."""
    mock_get_llm.return_value = _make_llm_mock("property_query")
    state = AgentState(query="apartments in Dubai Marina", conversation_history=[])
    result = memory_node(state)
    assert "first message" in result["conversation_context"].lower()
    assert result.get("route") is None  # no short-circuit


@patch("src.nodes.memory.get_llm")
def test_greeting_empty_history(mock_get_llm):
    """Greeting with empty history → short-circuit to greeting."""
    mock_get_llm.return_value = _make_llm_mock("greeting", "user says hi")
    state = AgentState(query="hi there", conversation_history=[])
    result = memory_node(state)
    assert result["route"] == "memory_greeting"


@patch("src.nodes.memory.get_llm")
def test_greeting_mid_conversation(mock_get_llm):
    """Greeting mid-conversation → still greeting, not property."""
    mock_get_llm.return_value = _make_llm_mock("greeting", "mid-convo greeting")
    state = AgentState(
        query="hello again",
        conversation_history=[
            {"role": "user", "content": "2BR in Marina"},
            {"role": "assistant", "content": "Found one."},
        ],
    )
    result = memory_node(state)
    assert result["route"] == "memory_greeting"


@patch("src.nodes.memory.get_llm")
def test_meta_question_detected(mock_get_llm):
    """Meta-question → short-circuit to memory_direct."""
    mock_get_llm.return_value = _make_llm_mock("meta_question", "asks about prior")
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
def test_normal_followup_is_property(mock_get_llm):
    """Follow-up property query → property_query, no short-circuit."""
    mock_get_llm.return_value = _make_llm_mock("property_query", "follow-up")
    state = AgentState(
        query="show me villas instead",
        conversation_history=[
            {"role": "user", "content": "2BR apartments in Dubai Marina"},
            {"role": "assistant", "content": "Found Marina Crest 2BR for AED 1.75M"},
        ],
    )
    result = memory_node(state)
    assert result.get("route") is None


@patch("src.nodes.memory.get_llm")
def test_unparseable_defaults_to_property(mock_get_llm):
    """Garbage LLM response → defaults to property_query."""
    mock_resp = MagicMock()
    mock_resp.content = "not valid json at all"
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_resp
    mock_get_llm.return_value = mock_llm

    state = AgentState(
        query="what was my last question?",
        conversation_history=[
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ],
    )
    result = memory_node(state)
    assert result.get("route") is None  # no short-circuit (safe default)


# ── route_after_memory ────────────────────────────────────────────────────────

def test_route_greeting():
    assert route_after_memory(AgentState(route="memory_greeting")) == "answer_generation"


def test_route_meta():
    assert route_after_memory(AgentState(route="memory_direct")) == "answer_generation"


def test_route_normal():
    assert route_after_memory(AgentState(route=None)) == "query_relevancy"


def test_route_property_pipeline():
    assert route_after_memory(AgentState(route="query_routing")) == "query_relevancy"
