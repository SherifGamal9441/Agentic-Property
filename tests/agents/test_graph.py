"""
Integration tests for the full LangGraph pipeline.

Three fake-state tests, one per graph path:

  Path A — Recommendation (query_routing → comparison_engine → reflection → answer_generation)
      Seeds state as if query_routing returned cached properties.
      Runs from memory onward through the full pipeline.

  Path B — Web search (web_search → answer_generation)
      Seeds state as if web_search ran and produced a summary.
      Runs the full graph.

  Path C — Rejection (query_relevancy already rejected)
      State has is_relevant=False and final_answer already set.
      Verifies graph does NOT call any downstream LLM when already rejected.

All LLM calls are mocked — no Ollama daemon needed.
"""

import json
import uuid
from unittest.mock import MagicMock, patch

from src.agents.graph import build_graph
from src.agents.state import AgentState

# ── Shared helpers ────────────────────────────────────────────────────────────

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


# ── Path A — Recommendation path ──────────────────────────────────────────────

@patch("src.nodes.answer_generation.get_llm")
@patch("src.nodes.query_routing.search_active_sync")
@patch("src.nodes.query_understanding.get_llm")
@patch("src.nodes.query_relevancy.get_llm")
def test_recommendation_path(
    mock_rel_llm, mock_und_llm,
    mock_search, mock_ans_llm
):
    """
    Full recommendation path with fake properties from active search.
    memory → query_relevancy → query_understanding → query_routing
    → comparison → reflection → answer.
    """
    # Relevancy: accept
    mock_rel_llm.return_value = _make_invoke_mock(
        json.dumps({"relevant": True, "failed_rule": None, "reason": "valid Dubai query"})
    )
    # Understanding: route to query_routing
    mock_und_llm.return_value = _make_invoke_mock(json.dumps({
        "parsed_query": {"location": "Dubai Marina", "bedrooms": 2},
        "route": "query_routing",
        "route_reason": "property recommendation",
    }))
    # Active search: return one property
    mock_search.return_value = [
        {"id": "prop-001", "title": "Marina Crest 2BR", "price": 1_750_000,
         "location": "Dubai Marina", "bedrooms": 2, "link": "https://example.test/1",
         "post_date": "2026-07-02", "amenities": ["sea view"]}
    ]
    # Answer generation
    mock_ans_llm.return_value = _make_stream_mock(FINAL_ANSWER_TOKENS)

    graph = build_graph(checkpointer=False)
    final_state = graph.invoke(
        {"query": "2BR in Dubai Marina, sea view, AED 1.8M"},
        {"configurable": {"thread_id": f"test-rec-{uuid.uuid4()}"}},
    )

    assert final_state["route"] == "query_routing"
    assert final_state["data_source"] == "active"
    assert final_state["data_intent"] == "recommend"
    assert final_state["comparison_result"] is not None
    assert final_state["reflection_output"]["ok"] is True
    assert final_state["final_answer"] == "Marina Crest is your best match."
    assert final_state["is_relevant"] is True
    # Conversation history should have 2 entries (user + assistant)
    assert len(final_state["conversation_history"]) == 2


# ── Path B — Web search path ──────────────────────────────────────────────────

@patch("src.nodes.answer_generation.get_llm")
@patch("src.nodes.query_understanding.get_llm")
@patch("src.nodes.query_relevancy.get_llm")
def test_web_search_path(mock_rel_llm, mock_und_llm, mock_ans_llm):
    """
    Web search path: memory → query_relevancy → query_understanding
    → web_search → answer_generation.
    We seed web_search_summary directly to bypass the real web_search sub-graph.
    """
    mock_rel_llm.return_value = _make_invoke_mock(
        json.dumps({"relevant": True, "failed_rule": None, "reason": "valid general question"})
    )
    mock_und_llm.return_value = _make_invoke_mock(json.dumps({
        "parsed_query": {"location": "Downtown Dubai"},
        "route": "web_search",
        "route_reason": "general trend question",
    }))
    mock_ans_llm.return_value = _make_stream_mock(["Rents ", "are ", "rising."])

    # Inject web_search_summary to simulate web_search sub-graph having already run
    with patch("src.agents.graph.create_web_search_agent") as mock_ws:
        mock_ws.return_value = lambda state: {
            "web_search_summary": "Rental prices in Downtown Dubai increased 12% in 2025."
        }

        graph = build_graph(checkpointer=False)
        final_state = graph.invoke(
            {"query": "What are rental trends in Downtown Dubai?"},
            {"configurable": {"thread_id": f"test-ws-{uuid.uuid4()}"}},
        )

    assert final_state["route"] == "web_search"
    assert final_state["final_answer"] == "Rents are rising."
    assert len(final_state["conversation_history"]) == 2


# ── Path C — Rejection path ───────────────────────────────────────────────────

@patch("src.nodes.query_understanding.get_llm")  # should NOT be called
@patch("src.nodes.query_relevancy.get_llm")
def test_rejection_path(mock_rel_llm, mock_und_llm):
    """
    Rejection path: memory → query_relevancy rejects → END immediately.
    query_understanding must NOT be called.
    """
    mock_rel_llm.return_value = _make_invoke_mock(
        json.dumps({"relevant": False, "failed_rule": "topic", "reason": "not real estate"})
    )

    graph = build_graph(checkpointer=False)
    final_state = graph.invoke(
        {"query": "What is the best pasta recipe?"},
        {"configurable": {"thread_id": f"test-rej-{uuid.uuid4()}"}},
    )

    assert final_state["is_relevant"] is False
    assert final_state["final_answer"] is not None
    assert "Dubai" in final_state["final_answer"] or "property" in final_state["final_answer"].lower()
    # query_understanding must NOT have been invoked
    mock_und_llm.assert_not_called()
