from datetime import date

from fastapi.testclient import TestClient

from src.data_service.app import app, build_market_context
from src.data_service.db_tables import HistoricalListing


def test_health_reports_database_backend_and_degraded_state():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["database_backend"] in {"postgresql", "sqlite"}
    assert isinstance(response.json()["degraded"], bool)
    assert "active_records" in response.json()
    assert "historical_records" in response.json()
    assert "active_snapshot_at" in response.json()


def test_market_context_uses_only_reported_historical_values():
    listings = [
        HistoricalListing(area_name="Dubai Marina", price=1_000_000, total_building_area_sqft=1_000, post_date=date(2025, 1, 1)),
        HistoricalListing(area_name="Dubai Marina", price=1_500_000, total_building_area_sqft=1_000, post_date=date(2025, 6, 1)),
        HistoricalListing(area_name="Dubai Marina", price=None, total_building_area_sqft=None, post_date=None),
    ]

    context = build_market_context("Dubai Marina", listings)

    assert context["record_count"] == 3
    assert context["price_min"] == 1_000_000
    assert context["price_per_sqft_max"] == 1_500
    assert context["period_start"] == date(2025, 1, 1)
