from src.agents.state import AgentState
from src.nodes.reflection import reflection_node, route_after_reflection


def test_reflection_accepts_auditable_active_snapshot_scoring():
    state = AgentState(
        query="brief",
        data_source="active",
        retrieved_properties=[{"id": "p-1", "link": "https://example.test/1", "post_date": "2026-07-02"}],
        comparison_result={"properties": [{
            "id": "p-1",
            "fit_score": 1,
            "evidence_coverage": 1,
            "suitability": "suitable",
            "evaluations": [{"priority": "must_have", "status": "matched"}],
        }]},
    )

    result = reflection_node(state)

    assert result["reflection_output"]["ok"] is True
    assert result["needs_retry"] is False


def test_reflection_never_routes_to_a_fake_retrieval_retry():
    assert route_after_reflection(AgentState(query="brief", needs_retry=True)) == "answer_generation"
