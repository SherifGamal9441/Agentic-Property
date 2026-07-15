from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from src.agent_api import app as api_module
from src.agent_api.app import RunRequest, _live_events, _property_payloads, app
from src.buyer_brief import BuyerBrief, Criterion


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
