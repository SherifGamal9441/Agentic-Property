from collections.abc import AsyncIterator
import json

from fastapi.testclient import TestClient
import pytest

from src.agent_api import app as api_module
from src.agent_api.app import RunRequest, _live_events, _property_payloads, app
from src.buyer_brief import BuyerBrief, Criterion


def _event_name(chunk: str) -> str:
    return chunk.splitlines()[0].removeprefix("event: ")


def _event_data(chunk: str) -> dict:
    return json.loads(next(line.removeprefix("data: ") for line in chunk.splitlines() if line.startswith("data: ")))


def _brief() -> dict:
    return BuyerBrief(
        original_query="Ready 2BR in Dubai Marina under AED 2M",
        criteria=[
            Criterion(id="area", label="Dubai Marina", priority="must_have", field="area", operator="contains", value="Dubai Marina"),
            Criterion(id="budget", label="Under AED 2M", priority="must_have", field="price", operator="lte", value=2_000_000),
        ],
    ).model_dump()


def test_interpret_endpoint_returns_a_validated_editable_brief(monkeypatch):
    monkeypatch.setattr(api_module, "_interpret_brief", lambda query: BuyerBrief.model_validate(_brief()))

    response = TestClient(app).post("/api/briefs/interpret", json={"query": "Ready 2BR in Dubai Marina under AED 2M"})

    assert response.status_code == 200
    assert response.json()["version"] == 1
    assert response.json()["criteria"][0]["priority"] == "must_have"


def test_runs_reject_raw_prompt_only_requests():
    response = TestClient(app).post("/api/runs", json={"query": "2BR in Marina"})

    assert response.status_code == 422


def test_property_payload_never_promotes_building_area_or_parking_to_unit_facts():
    payload = _property_payloads({
        "retrieved_properties": [{
            "id": 42,
            "property_id": "p-1",
            "area_name": "Dubai Marina",
            "price": 1_500_000,
            "total_building_area_sqft": 500_000,
            "total_parking_spaces": 300,
            "post_date": "2026-07-02",
            "link": "https://example.test/1",
        }],
        "comparison_result": {"properties": [{
            "id": "p-1",
            "fit_score": 1,
            "evidence_coverage": 1,
            "suitability": "suitable",
            "matched_criteria": [],
            "conflicting_criteria": [],
            "unknown_criteria": [],
            "unsupported_criteria": [],
            "evaluations": [],
        }]},
        "data_source": "active",
        "data_intent": "recommend",
    })[0]

    assert "size_sqft" not in payload
    assert "parking_spaces" not in payload
    assert payload["building_total_area_sqft"] == 500_000
    assert payload["building_total_parking_spaces"] == 300


def test_area_compare_requires_two_or_three_areas(monkeypatch):
    monkeypatch.setattr(api_module, "_market_context", lambda area, property_type=None, beds=None: {"area": area, "evidence_quality": "limited"})
    client = TestClient(app)

    assert client.post("/api/areas/compare", json={"areas": ["Dubai Marina"]}).status_code == 422
    response = client.post("/api/areas/compare", json={"areas": ["Dubai Marina", "Business Bay"]})
    assert response.status_code == 200
    assert [item["area"] for item in response.json()["areas"]] == ["Dubai Marina", "Business Bay"]


@pytest.mark.asyncio
async def test_property_run_streams_audited_counts_then_structured_guidance(monkeypatch):
    from src.agents import graph as graph_module
    from src.memory import long_term_memory as memory_module

    final_state = {
        "route": "property_search",
        "data_source": "active",
        "candidate_count": 20,
        "audited_count": 20,
        "retrieved_properties": [{
            "id": "p-1", "property_id": "p-1", "property_name": "Marina Residence",
            "area_name": "Dubai Marina", "price": 1_500_000, "post_date": "2026-07-02",
            "link": "https://example.test/p-1",
        }],
        "comparison_result": {"candidate_count": 20, "audited_count": 20, "properties": [{
            "id": "p-1", "fit_score": 1, "evidence_coverage": 1, "suitability": "suitable",
            "matched_criteria": ["area", "budget"], "conflicting_criteria": [],
            "unknown_criteria": [], "unsupported_criteria": [], "evaluations": [],
        }]},
        "buyer_guidance": {
            "version": 1, "outcome": "matches", "best_match_id": "p-1", "runner_up_id": None,
            "reasons": [{"property_id": "p-1", "code": "all_verifiable_criteria_matched", "criterion_ids": ["area", "budget"]}],
            "caveats": [], "next_action": "review_best_match",
        },
    }

    class FakeGraph:
        async def astream_events(self, *_args, **_kwargs):
            yield {"name": "LangGraph", "event": "on_chain_end", "data": {"output": final_state}}

    class FakeConnection:
        async def close(self):
            return None

    class FakeCheckpointer:
        conn = FakeConnection()

    async def fake_checkpointer():
        return FakeCheckpointer()

    monkeypatch.setattr(graph_module, "build_graph", lambda checkpointer: FakeGraph())
    monkeypatch.setattr(memory_module, "create_async_checkpointer", fake_checkpointer)

    chunks = [chunk async for chunk in _live_events(RunRequest(brief=BuyerBrief.model_validate(_brief()), thread_id="contract-test"))]

    assert [_event_name(chunk) for chunk in chunks] == ["run_started", "properties", "sources", "guidance", "run_completed"]
    properties = _event_data(chunks[1])
    assert properties["candidate_count"] == 20
    assert properties["audited_count"] == 20
    assert properties["total_matches"] == 1
    assert _event_data(chunks[3])["guidance"]["best_match_id"] == "p-1"
