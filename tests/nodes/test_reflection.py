"""
Tests for reflection_node and route_after_reflection.

Covers:
  - Clean comparison → ok=True → routes to answer_generation
  - Flawed comparison → ok=False, retry_count < max → needs_retry=True
  - Flawed comparison → ok=False, retry_count at max → no retry, routes to answer_generation
  - Unparseable LLM response → safe fallback, treated as failed
  - retry_count increments correctly
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.nodes.reflection import reflection_node, route_after_reflection

# ── Fixtures ──────────────────────────────────────────────────────────────────

GOOD_COMPARISON = {
    "properties": [
        {
            "id": "prop-001",
            "title": "Marina Crest 2BR",
            "fit_score": 0.9,
            "matched_criteria": ["location", "bedrooms", "sea view"],
            "unmatched_criteria": [],
            "price_assessment": "below_market",
        }
    ]
}

BAD_COMPARISON = {
    "properties": [
        {
            "id": "prop-001",
            "title": "Marina Crest 2BR",
            "fit_score": 0.95,        # suspiciously high
            "matched_criteria": [],    # but nothing matched — inconsistent!
            "unmatched_criteria": [],
            "price_assessment": None,  # missing required value
        }
    ]
}

REFLECTION_OK = json.dumps({"ok": True, "issues": [], "confidence": 0.9})
REFLECTION_FAIL = json.dumps({
    "ok": False,
    "issues": ["fit_score 0.95 but no matched criteria", "price_assessment is null"],
    "confidence": 0.3,
})

BASE_STATE = {
    "query": "2BR in Dubai Marina, AED 1.8M, sea view",
    "parsed_query": {},
    "retrieved_properties": [],
    "comparison_result": GOOD_COMPARISON,
    "reflection_output": None,
    "needs_retry": False,
    "retry_tool": None,
    "retry_count": 0,
    "final_answer": None,
}


def _mock_llm(response_content: str):
    mock_response = MagicMock()
    mock_response.content = response_content
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_response
    return mock_llm


# ── Tests: reflection_node ────────────────────────────────────────────────────

@patch("src.nodes.reflection.get_llm")
def test_reflection_ok_no_retry(mock_get_llm):
    """Passes good comparison → ok=True, needs_retry=False."""
    mock_get_llm.return_value = _mock_llm(REFLECTION_OK)

    result = reflection_node(BASE_STATE)

    assert result["reflection_output"]["ok"] is True
    assert result["reflection_output"]["issues"] == []
    assert result["needs_retry"] is False
    assert result["retry_count"] == 0   # no retry incremented


@patch("src.nodes.reflection.get_llm")
def test_reflection_fail_triggers_retry(mock_get_llm):
    """Flawed comparison + retries remaining → needs_retry=True, count incremented."""
    mock_get_llm.return_value = _mock_llm(REFLECTION_FAIL)
    state = {**BASE_STATE, "comparison_result": BAD_COMPARISON, "retry_count": 0}

    result = reflection_node(state)

    assert result["reflection_output"]["ok"] is False
    assert len(result["reflection_output"]["issues"]) == 2
    assert result["needs_retry"] is True
    assert result["retry_count"] == 1


@patch("src.nodes.reflection.get_llm")
def test_reflection_fail_at_max_retries_no_retry(mock_get_llm):
    """Flawed comparison but retry_count already at max → needs_retry=False."""
    mock_get_llm.return_value = _mock_llm(REFLECTION_FAIL)
    # max_retries defaults to 3 in settings; set retry_count to 3 (at cap)
    state = {**BASE_STATE, "comparison_result": BAD_COMPARISON, "retry_count": 3}

    result = reflection_node(state)

    assert result["needs_retry"] is False
    assert result["retry_count"] == 3   # not incremented past cap


@patch("src.nodes.reflection.get_llm")
def test_reflection_unparseable_response(mock_get_llm):
    """Unparseable LLM output → safe fallback with ok=False."""
    mock_get_llm.return_value = _mock_llm("I cannot audit this.")

    result = reflection_node(BASE_STATE)

    assert result["reflection_output"]["ok"] is False
    assert result["reflection_output"]["confidence"] == 0.0
    assert len(result["reflection_output"]["issues"]) > 0


# ── Tests: route_after_reflection ─────────────────────────────────────────────

def test_route_needs_retry_goes_to_tool_router():
    state = {**BASE_STATE, "needs_retry": True}
    assert route_after_reflection(state) == "tool_router"


def test_route_no_retry_goes_to_answer_generation():
    state = {**BASE_STATE, "needs_retry": False}
    assert route_after_reflection(state) == "answer_generation"
