from fastapi.testclient import TestClient

from src.data_service.app import app


def test_health_reports_database_backend_and_degraded_state():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["database_backend"] in {"postgresql", "sqlite"}
    assert isinstance(response.json()["degraded"], bool)
