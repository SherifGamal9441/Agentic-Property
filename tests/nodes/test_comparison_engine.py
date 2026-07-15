from src.agents.state import AgentState
from src.buyer_brief import BuyerBrief, Criterion
from src.nodes.comparison_engine import comparison_engine_node


def test_comparison_engine_uses_stable_sort_after_fit_and_coverage():
    brief = BuyerBrief(
        original_query="Marina under 2M",
        criteria=[
            Criterion(id="area", label="Marina", priority="must_have", field="area", operator="contains", value="Marina"),
            Criterion(id="budget", label="Under 2M", priority="must_have", field="price", operator="lte", value=2_000_000),
        ],
    )
    state = AgentState(
        query=brief.original_query,
        buyer_brief=brief,
        retrieved_properties=[
            {"id": "b", "area_name": "Dubai Marina", "price": 1_500_000},
            {"id": "a", "area_name": "Dubai Marina", "price": 1_500_000},
        ],
    )

    result = comparison_engine_node(state)

    assert [item["id"] for item in result["comparison_result"]["properties"]] == ["a", "b"]
    assert result["candidate_count"] == 2
    assert result["audited_count"] == 2


def test_deal_breaker_conflict_excludes_without_affecting_fit_weight():
    brief = BuyerBrief(
        original_query="No off-plan",
        criteria=[
            Criterion(id="ready", label="No off-plan", priority="deal_breaker", field="completion_status", operator="not_eq", value="under-construction"),
        ],
    )
    item = comparison_engine_node(AgentState(query=brief.original_query, buyer_brief=brief, retrieved_properties=[{"id": "x", "completion_status": "under-construction"}]))["comparison_result"]["properties"][0]

    assert item["suitability"] == "excluded"
    assert item["fit_score"] == 0
