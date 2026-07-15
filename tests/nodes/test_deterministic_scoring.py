import pytest

from src.agents.state import AgentState
from src.buyer_brief import BuyerBrief, Criterion
from src.nodes.comparison_engine import comparison_engine_node
from src.nodes.reflection import reflection_node


def _brief(*criteria: Criterion) -> BuyerBrief:
    return BuyerBrief(original_query="buyer brief", criteria=list(criteria))


def test_known_hard_conflict_excludes_and_unknown_must_have_is_conditional():
    brief = _brief(
        Criterion(id="area", label="Dubai Marina", priority="must_have", field="area", operator="contains", value="Dubai Marina"),
        Criterion(id="budget", label="Under AED 2M", priority="must_have", field="price", operator="lte", value=2_000_000),
        Criterion(id="furnished", label="Furnished", priority="nice_to_have", field="furnishing", operator="eq", value="Furnished"),
    )
    state = AgentState(
        query=brief.original_query,
        buyer_brief=brief,
        data_source="active",
        data_intent="recommend",
        retrieved_properties=[
            {"property_id": "conditional", "area_name": "Dubai Marina", "price": None, "furnishing": "Furnished", "link": "https://example.test/1", "post_date": "2026-07-02"},
            {"property_id": "excluded", "area_name": "Dubai Marina", "price": 2_500_000, "furnishing": "Furnished", "link": "https://example.test/2", "post_date": "2026-07-02"},
        ],
    )

    result = comparison_engine_node(state)["comparison_result"]["properties"]

    assert result[0]["id"] == "conditional"
    assert result[0]["suitability"] == "conditional"
    assert result[1]["id"] == "excluded"
    assert result[1]["suitability"] == "excluded"

    metadata = comparison_engine_node(state)
    assert metadata["candidate_count"] == 2
    assert metadata["audited_count"] == 2


def test_scoring_is_weighted_and_unsupported_criteria_do_not_enter_arithmetic():
    brief = _brief(
        Criterion(id="area", label="Dubai Marina", priority="must_have", field="area", operator="contains", value="Dubai Marina"),
        Criterion(id="furnished", label="Furnished", priority="nice_to_have", field="furnishing", operator="eq", value="Furnished"),
        Criterion(id="quiet", label="Quiet", priority="nice_to_have", field=None, operator=None, value=None, verifiable=False),
    )
    state = AgentState(
        query=brief.original_query,
        buyer_brief=brief,
        data_source="active",
        data_intent="recommend",
        retrieved_properties=[{"property_id": "one", "area_name": "Dubai Marina", "furnishing": "Unfurnished", "price": 1_000_000, "link": "https://example.test/1", "post_date": "2026-07-02"}],
    )

    property_result = comparison_engine_node(state)["comparison_result"]["properties"][0]

    assert property_result["fit_score"] == 0.75
    assert property_result["evidence_coverage"] == pytest.approx(2 / 3)
    assert property_result["unsupported_criteria"] == ["Quiet"]


def test_ready_and_completed_are_the_same_verified_status():
    brief = _brief(
        Criterion(
            id="ready",
            label="Ready home",
            priority="must_have",
            field="completion_status",
            operator="eq",
            value="Ready",
        ),
        Criterion(
            id="offplan",
            label="No off-plan",
            priority="deal_breaker",
            field="completion_status",
            operator="not_eq",
            value="Off-plan",
        ),
    )
    state = AgentState(
        query=brief.original_query,
        buyer_brief=brief,
        retrieved_properties=[{
            "property_id": "ready-home",
            "completion_status": "completed",
            "price": 1_500_000,
        }],
    )

    result = comparison_engine_node(state)["comparison_result"]["properties"][0]

    assert result["suitability"] == "suitable"
    assert result["conflicting_criteria"] == []


def test_reflection_withholds_invalid_identity_or_source_without_retry():
    state = AgentState(
        query="buyer brief",
        buyer_brief=BuyerBrief(original_query="buyer brief", criteria=[]),
        data_source="active",
        comparison_result={
            "properties": [
                {"id": "missing", "fit_score": 1.0, "evidence_coverage": 1.0, "suitability": "suitable", "evaluations": []}
            ]
        },
        retrieved_properties=[],
    )

    result = reflection_node(state)

    assert result["needs_retry"] is False
    assert result["reflection_output"]["ok"] is False
    assert result["withheld_count"] == 1
    assert result["comparison_result"]["properties"] == []
