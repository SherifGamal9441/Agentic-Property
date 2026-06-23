"""
Tests for query_routing_node.

Strategy: patch the internal tool stubs to return controlled data.
No LLM is involved in this node — it's pure routing logic.

Covers:
  - Cached tool returns results → data_source="cached", data_intent="recommend"
  - Cached empty, historical returns results → data_source="historical", data_intent="insights_only"
  - Both tools return empty → data_source="historical", data_intent="insights_only", empty list
"""

from unittest.mock import patch

from src.nodes.query_routing import query_routing_node
from src.agents.state import AgentState

_PARSED_QUERY = {
    "location": "Dubai Marina",
    "bedrooms": 2,
    "property_type": "apartment",
}

_FAKE_CACHED_PROPERTIES = [
    {"id": "c-001", "title": "Marina Crest 2BR", "price": 1_750_000, "area_sqm": 110,
     "location": "Dubai Marina", "bedrooms": 2, "amenities": ["sea view"]},
]

_FAKE_HISTORICAL_PROPERTIES = [
    {"id": "h-001", "title": "Old Marina Tower 2BR", "price": 1_200_000, "area_sqm": 95,
     "location": "Dubai Marina", "bedrooms": 2, "amenities": []},
]


def _make_state(**kwargs) -> AgentState:
    return AgentState(query="test", parsed_query=_PARSED_QUERY, **kwargs)


# ── Tests ─────────────────────────────────────────────────────────────────────

@patch("src.nodes.query_routing._call_cached_tool", return_value=_FAKE_CACHED_PROPERTIES)
def test_cached_tool_success(mock_cached):
    """Cached tool returns properties → recommend path."""
    result = query_routing_node(_make_state())

    assert result["data_source"] == "cached"
    assert result["data_intent"] == "recommend"
    assert len(result["retrieved_properties"]) == 1
    assert result["retrieved_properties"][0]["id"] == "c-001"


@patch("src.nodes.query_routing._call_historical_tool", return_value=_FAKE_HISTORICAL_PROPERTIES)
@patch("src.nodes.query_routing._call_cached_tool", return_value=[])
def test_cached_empty_falls_back_to_historical(mock_cached, mock_hist):
    """Cached returns nothing → historical fallback → insights_only."""
    result = query_routing_node(_make_state())

    assert result["data_source"] == "historical"
    assert result["data_intent"] == "insights_only"
    assert len(result["retrieved_properties"]) == 1
    assert result["retrieved_properties"][0]["id"] == "h-001"


@patch("src.nodes.query_routing._call_historical_tool", return_value=[])
@patch("src.nodes.query_routing._call_cached_tool", return_value=[])
def test_both_tools_empty(mock_cached, mock_hist):
    """Both tools empty → insights_only with empty list."""
    result = query_routing_node(_make_state())

    assert result["data_source"] == "historical"
    assert result["data_intent"] == "insights_only"
    assert result["retrieved_properties"] == []


@patch("src.nodes.query_routing._call_cached_tool", return_value=_FAKE_CACHED_PROPERTIES)
def test_historical_not_called_when_cached_succeeds(mock_cached):
    """Historical tool is never called if cached already returned results."""
    with patch("src.nodes.query_routing._call_historical_tool") as mock_hist:
        query_routing_node(_make_state())
        mock_hist.assert_not_called()
