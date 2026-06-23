"""
Tests for query_understanding_node and route_after_understanding.

Covers:
  - Recommendation query → route="query_routing", parsed_query has expected keys
  - General question → route="web_search"
  - Unparseable response → fail-safe defaults to web_search
  - route_after_understanding routing logic
"""

import json
from unittest.mock import MagicMock, patch

from src.nodes.query_understanding import query_understanding_node, route_after_understanding
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

@patch("src.nodes.query_understanding.get_llm")
def test_recommendation_query_routes_to_query_routing(mock_get_llm):
    """Specific property request → route=query_routing, parsed_query populated."""
    mock_get_llm.return_value = _mock_llm(json.dumps({
        "parsed_query": {
            "location": "JBR",
            "bedrooms": 2,
            "property_type": "apartment",
            "budget_aed": 1800000,
            "purpose": "buy",
        },
        "route": "query_routing",
        "route_reason": "User wants specific property results",
    }))

    result = query_understanding_node(_make_state("Find me a 2BR apartment in JBR for AED 1.8M"))

    assert result["route"] == "query_routing"
    assert result["parsed_query"]["location"] == "JBR"
    assert result["parsed_query"]["bedrooms"] == 2


@patch("src.nodes.query_understanding.get_llm")
def test_general_question_routes_to_web_search(mock_get_llm):
    """Market trend question → route=web_search."""
    mock_get_llm.return_value = _mock_llm(json.dumps({
        "parsed_query": {"location": "Dubai Marina"},
        "route": "web_search",
        "route_reason": "User asking about trends, not requesting listings",
    }))

    result = query_understanding_node(_make_state("What are rental trends in Dubai Marina?"))

    assert result["route"] == "web_search"


@patch("src.nodes.query_understanding.get_llm")
def test_unparseable_response_defaults_to_web_search(mock_get_llm):
    """Unparseable LLM output → fail-safe: route=web_search, empty parsed_query."""
    mock_get_llm.return_value = _mock_llm("I cannot parse this query.")

    result = query_understanding_node(_make_state("Some ambiguous query"))

    assert result["route"] == "web_search"
    assert result["parsed_query"] == {}


@patch("src.nodes.query_understanding.get_llm")
def test_only_route_and_parsed_query_returned(mock_get_llm):
    """Node only mutates route and parsed_query — nothing else."""
    mock_get_llm.return_value = _mock_llm(json.dumps({
        "parsed_query": {"location": "Downtown Dubai"},
        "route": "query_routing",
        "route_reason": "recommendation request",
    }))

    result = query_understanding_node(_make_state("Find villas in Downtown Dubai"))

    assert set(result.keys()) == {"parsed_query", "route"}


# ── Tests: router ─────────────────────────────────────────────────────────────

def test_route_query_routing():
    state = AgentState(query="test", route="query_routing")
    assert route_after_understanding(state) == "query_routing"


def test_route_web_search():
    state = AgentState(query="test", route="web_search")
    assert route_after_understanding(state) == "web_search"


def test_route_none_defaults_to_web_search():
    state = AgentState(query="test", route=None)
    assert route_after_understanding(state) == "web_search"
