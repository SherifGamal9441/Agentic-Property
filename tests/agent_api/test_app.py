from fastapi.testclient import TestClient

from src.agent_api.app import app


def test_demo_run_streams_ranked_property_cards():
    response = TestClient(app).post(
        "/api/runs",
        json={
            "query": "Find a 2 bedroom apartment in Dubai Marina",
            "mode": "demo",
            "thread_id": "test-demo-thread",
        },
    )

    assert response.status_code == 200
    assert "event: properties" in response.text
    assert '"title":"Marina Vista Residence"' in response.text
    assert '"data_intent":"recommend"' in response.text
