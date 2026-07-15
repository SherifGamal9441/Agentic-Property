"""Unit tests for deterministic memory restoration."""

from src.agents.state import AgentState
from src.nodes.memory import (
    memory_node,
    _format_history_for_context,
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


# ── memory_node ──────────────────────────────────────────────────────────────

def test_memory_restores_context_without_changing_route():
    state = AgentState(
        query="Ready 2BR in Dubai Marina",
        conversation_history=[{"role": "user", "content": "Previous brief"}],
    )

    result = memory_node(state)

    assert "Previous brief" in result["conversation_context"]
    assert result["route"] is None


def test_empty_history_uses_first_message_context():
    state = AgentState(query="apartments in Dubai Marina", conversation_history=[])
    result = memory_node(state)
    assert "first message" in result["conversation_context"].lower()
    assert result["route"] is None
