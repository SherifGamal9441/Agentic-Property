from unittest.mock import patch

import pytest

from src.agents.state import AgentState
from src.nodes.query_routing import query_routing_node


def _state() -> AgentState:
    return AgentState(query="test", parsed_query={"area_name": "Dubai Marina", "limit": 20})


@patch("src.nodes.query_routing._call_active_tool", return_value=([{"id": "active-1"}], None))
def test_active_snapshot_success(mock_active):
    result = query_routing_node(_state())

    assert result["data_source"] == "active"
    assert result["data_intent"] == "recommend"
    assert result["retrieved_properties"] == [{"id": "active-1"}]


@patch("src.nodes.query_routing._call_active_tool", return_value=([], None))
def test_no_result_does_not_fall_back_to_historical(mock_active):
    result = query_routing_node(_state())

    assert result["data_source"] == "active"
    assert result["data_intent"] == "recommend"
    assert result["retrieved_properties"] == []


@patch("src.nodes.query_routing._call_active_tool", return_value=([], "transport failed"))
def test_transport_failure_is_not_disguised_as_zero_matches(mock_active):
    with pytest.raises(RuntimeError, match="snapshot"):
        query_routing_node(_state())
