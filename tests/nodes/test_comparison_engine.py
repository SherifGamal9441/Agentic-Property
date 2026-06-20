"""
Tests for comparison_engine_node.

Strategy: mock the LLM so no Ollama daemon is needed.
We test that the node correctly:
  - builds state from the LLM's JSON response
  - handles a clean JSON response
  - gracefully handles a markdown-fenced JSON response (common LLM quirk)
  - gracefully handles fully unparseable output
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.nodes.comparison_engine import comparison_engine_node

# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_PARSED_QUERY = {
    "location": "Dubai Marina",
    "property_type": "apartment",
    "bedrooms": 2,
    "budget_aed": 1_800_000,
    "amenities": ["sea view"],
}

SAMPLE_PROPERTIES = [
    {
        "id": "prop-001",
        "title": "Marina Crest 2BR",
        "price": 1_750_000,
        "area_sqm": 110,
        "location": "Dubai Marina",
        "bedrooms": 2,
        "amenities": ["sea view", "gym"],
    },
    {
        "id": "prop-002",
        "title": "Marina Gate 2BR",
        "price": 1_900_000,
        "area_sqm": 105,
        "location": "Dubai Marina",
        "bedrooms": 2,
        "amenities": ["gym"],
    },
]

EXPECTED_COMPARISON = {
    "properties": [
        {
            "id": "prop-001",
            "title": "Marina Crest 2BR",
            "fit_score": 0.9,
            "matched_criteria": ["location", "bedrooms", "sea view"],
            "unmatched_criteria": [],
            "price_assessment": "below_market",
        },
        {
            "id": "prop-002",
            "title": "Marina Gate 2BR",
            "fit_score": 0.6,
            "matched_criteria": ["location", "bedrooms"],
            "unmatched_criteria": ["sea view", "budget"],
            "price_assessment": "above_market",
        },
    ]
}

BASE_STATE = {
    "query": "2BR in Dubai Marina, AED 1.8M, sea view",
    "parsed_query": SAMPLE_PARSED_QUERY,
    "retrieved_properties": SAMPLE_PROPERTIES,
    "comparison_result": None,
    "reflection_output": None,
    "needs_retry": False,
    "retry_tool": None,
    "retry_count": 0,
    "final_answer": None,
}


def _mock_llm(response_content: str):
    """Return a mock LLM that always yields response_content."""
    mock_response = MagicMock()
    mock_response.content = response_content
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_response
    return mock_llm


# ── Tests ─────────────────────────────────────────────────────────────────────

@patch("src.nodes.comparison_engine.get_llm")
def test_comparison_engine_clean_json(mock_get_llm):
    """Node correctly parses a clean JSON response from the LLM."""
    mock_get_llm.return_value = _mock_llm(json.dumps(EXPECTED_COMPARISON))

    result = comparison_engine_node(BASE_STATE)

    assert "comparison_result" in result
    props = result["comparison_result"]["properties"]
    assert len(props) == 2
    assert props[0]["id"] == "prop-001"
    assert props[0]["fit_score"] == 0.9
    assert props[1]["price_assessment"] == "above_market"


@patch("src.nodes.comparison_engine.get_llm")
def test_comparison_engine_markdown_fenced_json(mock_get_llm):
    """Node strips markdown code fences that some models add despite instructions."""
    fenced = f"```json\n{json.dumps(EXPECTED_COMPARISON)}\n```"
    mock_get_llm.return_value = _mock_llm(fenced)

    result = comparison_engine_node(BASE_STATE)

    assert "comparison_result" in result
    assert len(result["comparison_result"]["properties"]) == 2


@patch("src.nodes.comparison_engine.get_llm")
def test_comparison_engine_unparseable_response(mock_get_llm):
    """Node returns a safe fallback when LLM output is completely unparseable."""
    mock_get_llm.return_value = _mock_llm("I cannot compare these properties.")

    result = comparison_engine_node(BASE_STATE)

    assert "comparison_result" in result
    assert result["comparison_result"]["properties"] == []
    assert "_parse_error" in result["comparison_result"]


@patch("src.nodes.comparison_engine.get_llm")
def test_comparison_engine_returns_only_comparison_result(mock_get_llm):
    """Node only mutates comparison_result — not other state fields."""
    mock_get_llm.return_value = _mock_llm(json.dumps(EXPECTED_COMPARISON))

    result = comparison_engine_node(BASE_STATE)

    assert set(result.keys()) == {"comparison_result"}
