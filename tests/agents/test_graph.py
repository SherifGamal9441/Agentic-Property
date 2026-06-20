"""
Integration test for the full P2 LangGraph pipeline.

Runs the compiled graph end-to-end with all LLM calls mocked,
verifying that state flows correctly through:
    comparison_engine → reflection → answer_generation
"""

import json
from unittest.mock import MagicMock, patch

import pytest

# ── Shared mock helpers ───────────────────────────────────────────────────────

COMPARISON_RESULT = {
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

REFLECTION_OK = {"ok": True, "issues": [], "confidence": 0.9}

FINAL_ANSWER_TOKENS = ["Marina ", "Crest ", "is ", "your ", "best ", "match."]

INITIAL_STATE = {
    "query": "2BR in Dubai Marina, AED 1.8M, sea view",
    "parsed_query": {
        "location": "Dubai Marina",
        "property_type": "apartment",
        "bedrooms": 2,
        "budget_aed": 1_800_000,
        "amenities": ["sea view"],
    },
    "retrieved_properties": [
        {
            "id": "prop-001",
            "title": "Marina Crest 2BR",
            "price": 1_750_000,
            "area_sqm": 110,
            "location": "Dubai Marina",
            "bedrooms": 2,
            "amenities": ["sea view", "gym"],
        }
    ],
    "comparison_result": None,
    "reflection_output": None,
    "needs_retry": False,
    "retry_tool": None,
    "retry_count": 0,
    "final_answer": None,
}


def _make_invoke_mock(content: str):
    resp = MagicMock()
    resp.content = content
    llm = MagicMock()
    llm.invoke.return_value = resp
    return llm


def _make_stream_mock(tokens: list[str]):
    chunks = [MagicMock(content=t) for t in tokens]
    llm = MagicMock()
    llm.stream.return_value = iter(chunks)
    return llm


# ── Tests ─────────────────────────────────────────────────────────────────────

@patch("src.nodes.answer_generation.get_llm")
@patch("src.nodes.reflection.get_llm")
@patch("src.nodes.comparison_engine.get_llm")
def test_full_pipeline_happy_path(mock_comp_llm, mock_refl_llm, mock_ans_llm):
    """
    Happy path: good comparison → reflection passes → final answer generated.
    Verifies state has comparison_result, reflection_output, and final_answer.
    """
    mock_comp_llm.return_value = _make_invoke_mock(json.dumps(COMPARISON_RESULT))
    mock_refl_llm.return_value = _make_invoke_mock(json.dumps(REFLECTION_OK))
    mock_ans_llm.return_value = _make_stream_mock(FINAL_ANSWER_TOKENS)

    # Import after patching to ensure mocks are active
    from src.agents.graph import build_graph
    graph = build_graph()
    final_state = graph.invoke(INITIAL_STATE)

    assert final_state["comparison_result"] is not None
    assert final_state["reflection_output"]["ok"] is True
    assert final_state["final_answer"] == "Marina Crest is your best match."
    assert final_state["needs_retry"] is False


@patch("src.nodes.reflection.get_llm")
@patch("src.nodes.comparison_engine.get_llm")
def test_full_pipeline_retry_path(mock_comp_llm, mock_refl_llm):
    """
    Retry path: reflection fails → needs_retry=True → graph ends (signals upstream).
    final_answer must be None since answer_generation was never reached.
    """
    bad_comparison = {"properties": []}
    reflection_fail = {"ok": False, "issues": ["no properties compared"], "confidence": 0.1}

    mock_comp_llm.return_value = _make_invoke_mock(json.dumps(bad_comparison))
    mock_refl_llm.return_value = _make_invoke_mock(json.dumps(reflection_fail))

    from src.agents.graph import build_graph
    graph = build_graph()
    final_state = graph.invoke(INITIAL_STATE)

    assert final_state["needs_retry"] is True
    assert final_state["final_answer"] is None
    assert final_state["retry_count"] == 1
