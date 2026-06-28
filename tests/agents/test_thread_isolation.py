"""Integration test: thread isolation across separate graph invocations.

Verifies that two different thread_ids produce independent conversation histories
and that history accumulates correctly across multiple turns within the same thread.
"""

import json
import uuid
from unittest.mock import MagicMock, patch

from src.agents.graph import build_graph

COMPARISON_RESULT = {
    "properties": [{
        "id": "prop-001", "title": "Marina Crest 2BR",
        "fit_score": 0.9, "matched_criteria": ["location", "bedrooms"],
        "unmatched_criteria": [], "price_assessment": "below_market",
    }]
}
REFLECTION_OK = {"ok": True, "issues": [], "confidence": 0.9}


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


@patch("src.nodes.answer_generation.get_llm")
@patch("src.nodes.reflection.get_llm")
@patch("src.nodes.comparison_engine.get_llm")
@patch("src.nodes.query_routing.search_active_sync")
@patch("src.nodes.query_understanding.get_llm")
@patch("src.nodes.query_relevancy.get_llm")
@patch("src.nodes.memory.get_llm")
def test_thread_isolation(
    mock_mem_llm, mock_rel_llm, mock_und_llm,
    mock_search, mock_comp_llm, mock_refl_llm, mock_ans_llm,
):
    """Two different thread_ids produce independent conversation histories."""
    # Memory node: no meta detection (empty history on first turn)
    mock_mem_llm.return_value = _make_invoke_mock(json.dumps({"is_meta": False}))
    # Relevancy: accept
    mock_rel_llm.return_value = _make_invoke_mock(
        json.dumps({"relevant": True, "failed_rule": None, "reason": "valid"})
    )
    # Understanding: route to query_routing
    mock_und_llm.return_value = _make_invoke_mock(json.dumps({
        "parsed_query": {"area_name": "Dubai Marina"},
        "route": "query_routing",
        "route_reason": "property search",
    }))
    # Active search: return one property
    mock_search.return_value = [
        {"id": "prop-001", "title": "Marina Crest 2BR", "price": 1_750_000,
         "area_sqm": 110, "location": "Dubai Marina", "bedrooms": 2}
    ]
    mock_comp_llm.return_value = _make_invoke_mock(json.dumps(COMPARISON_RESULT))
    mock_refl_llm.return_value = _make_invoke_mock(json.dumps(REFLECTION_OK))

    graph = build_graph()

    thread_a = f"thread-a-{uuid.uuid4()}"
    thread_b = f"thread-b-{uuid.uuid4()}"

    # ── Turn 1 — Thread A ──────────────────────────────────────────────────
    mock_ans_llm.return_value = _make_stream_mock(["Marina ", "Crest ", "recommended."])
    result_a1 = graph.invoke(
        {"query": "2BR in Dubai Marina"},
        {"configurable": {"thread_id": thread_a}},
    )
    assert "Marina Crest" in result_a1["final_answer"]
    assert len(result_a1["conversation_history"]) == 2  # user + assistant

    # ── Turn 1 — Thread B (independent) ─────────────────────────────────────
    mock_ans_llm.return_value = _make_stream_mock(["Villa ", "found ", "in ", "Palm."])
    result_b1 = graph.invoke(
        {"query": "villas in Palm Jumeirah"},
        {"configurable": {"thread_id": thread_b}},
    )
    assert "Palm" in result_b1["final_answer"]
    assert len(result_b1["conversation_history"]) == 2  # independent history

    # ── Turn 2 — Thread A (accumulates) ─────────────────────────────────────
    mock_ans_llm.return_value = _make_stream_mock(["Second ", "answer."])
    # Memory node now has history → needs meta-detection response
    mock_mem_llm.return_value = _make_invoke_mock(json.dumps({"is_meta": False}))

    result_a2 = graph.invoke(
        {"query": "what about 3BR?"},
        {"configurable": {"thread_id": thread_a}},
    )
    assert len(result_a2["conversation_history"]) == 4  # 2 prior + 2 new

    # ── Verify Thread B is still independent ────────────────────────────────
    # Re-invoke thread B to get its current state
    mock_ans_llm.return_value = _make_stream_mock(["Third ", "answer."])
    mock_mem_llm.return_value = _make_invoke_mock(json.dumps({"is_meta": False}))

    result_b2 = graph.invoke(
        {"query": "show me more villas"},
        {"configurable": {"thread_id": thread_b}},
    )
    # Thread B should have accumulated independently: 2 prior + 2 new = 4
    assert len(result_b2["conversation_history"]) == 4

    # Thread A history should still be at 4, not affected by thread B
    result_a3 = graph.invoke(
        {"query": "thanks!"},
        {"configurable": {"thread_id": thread_a}},
    )
    assert len(result_a3["conversation_history"]) == 6  # 4 prior + 2 new

    # Thread A history contains only its own queries
    history_strings = [
        m["content"] for m in result_a3["conversation_history"]
        if m["role"] == "user"
    ]
    assert "2BR in Dubai Marina" in history_strings
    assert "what about 3BR?" in history_strings
    assert "thanks!" in history_strings
    assert "villas in Palm Jumeirah" not in history_strings  # thread B query
