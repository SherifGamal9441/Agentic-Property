"""
Tests for answer_generation_node.

Covers:
  - Final answer is populated in state
  - Streaming chunks are assembled correctly
  - Reflection issues are referenced when present
  - Node handles missing reflection_output gracefully
"""

from unittest.mock import MagicMock, patch

import pytest

from src.nodes.answer_generation import answer_generation_node, _build_messages, _format_comparison_for_prompt
from src.agents.state import AgentState
from src.buyer_brief import BuyerBrief, Criterion

# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_COMPARISON = {
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
    "parsed_query": {"location": "Dubai Marina", "bedrooms": 2},
    "retrieved_properties": [],
    "comparison_result": SAMPLE_COMPARISON,
    "reflection_output": {"ok": True, "issues": [], "confidence": 0.9},
    "needs_retry": False,
    "retry_tool": None,
    "retry_count": 0,
    "final_answer": None,
}

STREAMED_TOKENS = ["Marina ", "Crest ", "is ", "your ", "best ", "match."]


def _mock_streaming_llm(tokens: list[str]):
    """Return a mock LLM whose .stream() yields chunk objects."""
    chunks = []
    for token in tokens:
        chunk = MagicMock()
        chunk.content = token
        chunks.append(chunk)

    mock_llm = MagicMock()
    mock_llm.stream.return_value = iter(chunks)
    return mock_llm


# ── Tests ─────────────────────────────────────────────────────────────────────

@patch("src.nodes.answer_generation.get_llm")
def test_answer_generation_populates_final_answer(mock_get_llm):
    """Node assembles streamed tokens into final_answer."""
    mock_get_llm.return_value = _mock_streaming_llm(STREAMED_TOKENS)

    result = answer_generation_node(AgentState(**BASE_STATE))

    assert "final_answer" in result
    assert result["final_answer"] == "Marina Crest is your best match."


@patch("src.nodes.answer_generation.get_llm")
def test_answer_generation_only_mutates_final_answer(mock_get_llm):
    """Node returns final_answer and conversation_history — does not overwrite other state fields."""
    mock_get_llm.return_value = _mock_streaming_llm(STREAMED_TOKENS)

    result = answer_generation_node(AgentState(**BASE_STATE))

    assert set(result.keys()) == {"final_answer", "conversation_history"}


@patch("src.nodes.answer_generation.get_llm")
def test_answer_generation_handles_missing_reflection(mock_get_llm):
    """Node works correctly even when reflection_output is None."""
    mock_get_llm.return_value = _mock_streaming_llm(STREAMED_TOKENS)
    state = {**BASE_STATE, "reflection_output": None}

    result = answer_generation_node(AgentState(**state))

    assert result["final_answer"] == "Marina Crest is your best match."


# ── Tests: _format_comparison_for_prompt ──────────────────────────────────────

def test_format_sorts_by_fit_score_descending():
    """Best property (highest fit_score) appears first in the formatted block."""
    formatted = _format_comparison_for_prompt(SAMPLE_COMPARISON)
    idx_001 = formatted.index("prop-001")
    idx_002 = formatted.index("prop-002")
    assert idx_001 < idx_002   # prop-001 (score 0.9) before prop-002 (score 0.6)


def test_format_none_comparison_returns_placeholder():
    assert _format_comparison_for_prompt(None) == "No comparison data available."


def test_format_empty_properties_returns_placeholder():
    assert _format_comparison_for_prompt({"properties": []}) == "No properties were compared."


def test_excluded_properties_never_enter_buyer_guidance():
    comparison = {
        "properties": [{
            "id": "excluded",
            "title": "Do not recommend",
            "fit_score": 0.9,
            "suitability": "excluded",
        }]
    }
    state = AgentState(
        query="Ready home",
        retrieved_properties=[{"property_id": "excluded"}],
        comparison_result=comparison,
    )

    formatted = _format_comparison_for_prompt(comparison)
    messages = _build_messages(state)

    assert "Do not recommend" not in formatted
    assert "No property in the frozen listing snapshot" in messages[1].content


@patch("src.nodes.answer_generation.get_llm")
def test_property_guidance_is_structured_and_repaired_once(mock_get_llm):
    brief = BuyerBrief(
        original_query="Home in Dubai Marina",
        criteria=[Criterion(id="area", label="Dubai Marina", priority="must_have", field="area", operator="contains", value="Dubai Marina")],
    )
    state = AgentState(
        query=brief.original_query,
        buyer_brief=brief,
        route="query_routing",
        data_intent="recommend",
        comparison_result={"properties": [{
            "id": "one",
            "title": "Marina Home",
            "suitability": "suitable",
            "fit_score": 1,
            "evidence_coverage": 1,
            "evaluations": [{"criterion_id": "area", "status": "matched"}],
        }]},
    )
    llm = MagicMock()
    llm.invoke.side_effect = [
        MagicMock(content="not json"),
        MagicMock(content='{"version":1,"outcome":"matches","best_match_id":"one","runner_up_id":null,"reasons":[],"caveats":[],"next_action":"review_best_match"}'),
    ]
    mock_get_llm.return_value = llm

    result = answer_generation_node(state)

    assert result["buyer_guidance"].best_match_id == "one"
    assert result["final_answer"] == "Best match: Marina Home. No known criterion gaps in the captured fields."
    assert llm.invoke.call_count == 2
