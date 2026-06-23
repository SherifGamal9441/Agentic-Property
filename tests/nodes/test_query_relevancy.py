"""
Tests for query_relevancy_node and route_after_relevancy.

Covers:
  - Valid Dubai property query → is_relevant=True, no final_answer set
  - Non-Dubai location → is_relevant=False, rejection mentions Dubai
  - Off-topic query → is_relevant=False, rejection explains what agent can do
  - Unparseable LLM response → fail-safe, is_relevant=True (don't block users)
  - route_after_relevancy routing logic
"""

import json
from unittest.mock import MagicMock, patch

from src.nodes.query_relevancy import query_relevancy_node, route_after_relevancy
from src.agents.state import AgentState


def _mock_llm(response_content: str):
    resp = MagicMock()
    resp.content = response_content
    llm = MagicMock()
    llm.invoke.return_value = resp
    return llm


def _make_state(query: str) -> AgentState:
    return AgentState(query=query)


# ── Tests: node ───────────────────────────────────────────────────────────────

@patch("src.nodes.query_relevancy.get_llm")
def test_valid_dubai_property_query_is_accepted(mock_get_llm):
    """Dubai property query passes both rules → is_relevant=True."""
    mock_get_llm.return_value = _mock_llm(
        json.dumps({"relevant": True, "failed_rule": None, "reason": "Dubai apartment query"})
    )
    result = query_relevancy_node(_make_state("Find me a 2BR apartment in Dubai Marina"))

    assert result["is_relevant"] is True
    assert "final_answer" not in result


@patch("src.nodes.query_relevancy.get_llm")
def test_non_dubai_location_is_rejected(mock_get_llm):
    """Non-Dubai location fails geography rule → is_relevant=False, rejection mentions Dubai."""
    mock_get_llm.return_value = _mock_llm(
        json.dumps({"relevant": False, "failed_rule": "geography", "reason": "Cairo is not Dubai"})
    )
    result = query_relevancy_node(_make_state("Find me an apartment in Cairo"))

    assert result["is_relevant"] is False
    assert "Dubai" in result["final_answer"]
    assert "can" in result["final_answer"].lower()   # explains what it CAN do


@patch("src.nodes.query_relevancy.get_llm")
def test_off_topic_query_is_rejected(mock_get_llm):
    """Non-property query fails topic rule → is_relevant=False, rejection explains scope."""
    mock_get_llm.return_value = _mock_llm(
        json.dumps({"relevant": False, "failed_rule": "topic", "reason": "cooking is not real estate"})
    )
    result = query_relevancy_node(_make_state("What is the best pasta recipe?"))

    assert result["is_relevant"] is False
    assert result["final_answer"]                    # message is non-empty
    assert "property" in result["final_answer"].lower() or "real estate" in result["final_answer"].lower()


@patch("src.nodes.query_relevancy.get_llm")
def test_both_rules_fail(mock_get_llm):
    """Query fails both rules → uses 'both' rejection template."""
    mock_get_llm.return_value = _mock_llm(
        json.dumps({"relevant": False, "failed_rule": "both", "reason": "unrelated"})
    )
    result = query_relevancy_node(_make_state("Who won the Champions League?"))

    assert result["is_relevant"] is False
    assert result["final_answer"]


@patch("src.nodes.query_relevancy.get_llm")
def test_unparseable_response_defaults_to_relevant(mock_get_llm):
    """Unparseable LLM output → fail-safe: is_relevant=True (don't block users)."""
    mock_get_llm.return_value = _mock_llm("I cannot classify this.")

    result = query_relevancy_node(_make_state("Some query"))

    assert result["is_relevant"] is True


# ── Tests: router ─────────────────────────────────────────────────────────────

def test_route_relevant_goes_to_query_understanding():
    state = AgentState(query="test", is_relevant=True)
    assert route_after_relevancy(state) == "query_understanding"


def test_route_irrelevant_goes_to_end():
    state = AgentState(query="test", is_relevant=False)
    assert route_after_relevancy(state) == "end"
