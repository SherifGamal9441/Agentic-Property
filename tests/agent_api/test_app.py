from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
from types import ModuleType

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


def test_market_context_proxy_forwards_available_comparable_facts():
    with patch("src.agent_api.app._market_context", return_value={"record_count": 2}) as market_context:
        response = TestClient(app).get("/api/market-context?area=Dubai%20Marina&property_type=Apartments&beds=2")

    assert response.status_code == 200
    market_context.assert_called_once_with("Dubai Marina", "Apartments", 2)


def test_conversation_endpoint_returns_only_saved_messages(monkeypatch):
    class Connection:
        async def close(self):
            pass

    class Checkpointer:
        conn = Connection()

    class Graph:
        async def aget_state(self, _config):
            return type("State", (), {"values": {"conversation_history": [
                {"role": "user", "content": "2BR in Dubai Marina"},
                {"role": "assistant", "content": "Here are matches."},
                {"role": "system", "content": "hidden"},
            ]}})()

    async def create_checkpointer():
        return Checkpointer()

    memory_module = ModuleType("src.memory.long_term_memory")
    memory_module.create_async_checkpointer = create_checkpointer
    graph_module = ModuleType("src.agents.graph")
    graph_module.build_graph = lambda checkpointer: Graph()
    monkeypatch.setitem(sys.modules, "src.memory.long_term_memory", memory_module)
    monkeypatch.setitem(sys.modules, "src.agents.graph", graph_module)

    response = TestClient(app).get("/api/conversations/8f9d67d9-61de-44d9-a95d-8d0c5c8a9d4f")

    assert response.status_code == 200
    assert response.json()["messages"] == [
        {"role": "user", "content": "2BR in Dubai Marina"},
        {"role": "assistant", "content": "Here are matches."},
    ]
