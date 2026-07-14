"""Full agent graph routing with active data and mocked model boundaries."""

from unittest.mock import MagicMock, patch

from src.agents.graph import build_graph


ACTIVE_PROPERTIES = [{
    "id": "prop-001",
    "title": "Marina Crest 2BR Apartment",
    "price": 1_750_000,
    "area_name": "Dubai Marina",
    "beds": 2,
}]


def _llm(content: str) -> MagicMock:
    response = MagicMock(content=content)
    llm = MagicMock()
    llm.invoke.return_value = response
    return llm


@patch("src.nodes.answer_generation.get_llm")
@patch("src.nodes.reflection.get_llm")
@patch("src.nodes.comparison_engine.get_llm")
@patch("src.nodes.query_routing._call_historical_tool", return_value=([], None))
@patch("src.nodes.query_routing._call_active_tool", return_value=(ACTIVE_PROPERTIES, None))
@patch("src.nodes.query_understanding.get_llm")
@patch("src.nodes.query_relevancy.get_llm")
@patch("src.nodes.memory.get_llm")
def test_full_pipeline_uses_active_data(
    mock_memory, mock_relevancy, mock_understanding, _mock_active, _mock_historical,
    mock_comparison, mock_reflection, mock_answer,
):
    mock_memory.return_value = _llm('{"category":"property_query"}')
    mock_relevancy.return_value = _llm('{"relevant":true}')
    mock_understanding.return_value = _llm('{"parsed_query":{"area_name":"Dubai Marina"},"route":"query_routing"}')
    mock_comparison.return_value = _llm('{"properties":[{"id":"prop-001","title":"Marina Crest 2BR Apartment","fit_score":0.9,"matched_criteria":["location"],"unmatched_criteria":[],"price_assessment":"fair"}]}')
    mock_reflection.return_value = _llm('{"ok":true,"issues":[],"confidence":0.9}')
    mock_answer.return_value.stream.return_value = iter([MagicMock(content="A supported result.")])

    state = build_graph(checkpointer=False).invoke({"query": "2BR in Dubai Marina"})

    assert state["is_relevant"] is True
    assert state["route"] == "query_routing"
    assert state["data_source"] == "active"
    assert state["data_intent"] == "recommend"
    assert state["comparison_result"]["properties"][0]["id"] == "prop-001"
    assert state["final_answer"] == "A supported result."
