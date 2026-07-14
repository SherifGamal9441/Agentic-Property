from fastapi.testclient import TestClient

from src.agent_api.app import _property_payloads, _safe_failure, app


def test_property_payload_exposes_snapshot_evidence_and_safe_nulls():
    payload = _property_payloads({
        "parsed_query": {"area_name": "Dubai Marina", "property_beds_minimum": 2},
        "retrieved_properties": [{
            "property_id": "p-1",
            "building_name": "Marina Crest",
            "area_name": "Dubai Marina",
            "beds": 2,
            "price": None,
            "post_date": "2026-07-01",
            "latitude": None,
            "longitude": None,
            "link": "https://example.test/p-1",
        }],
        "comparison_result": {"properties": [{"property_id": "p-1"}]},
        "data_source": "active",
        "data_intent": "recommend",
    })

    assert payload[0]["data_status"] == "active_dataset_listing"
    assert payload[0]["observed_at"] == "2026-07-01"
    assert payload[0]["price"] is None
    assert payload[0]["location_status"] == "unavailable"
    assert payload[0]["score_factors"] == ["Matches Dubai Marina", "Meets 2+ bedrooms"]


def test_safe_failure_hides_internal_exception_text():
    assert _safe_failure(RuntimeError("secret database host")) == {
        "code": "agent_unavailable",
        "message": "Property research is temporarily unavailable. Please try again.",
        "retryable": True,
    }


def test_health_endpoint_is_available():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
