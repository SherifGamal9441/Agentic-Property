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


def test_market_context_uses_robust_price_evidence_without_building_area_unit_prices():
    listings = [
        HistoricalListing(area_name="Dubai Marina", price=1_000_000, building_total_area_sqft=1_000, post_date=date(2025, 1, 1)),
        HistoricalListing(area_name="Dubai Marina", price=1_500_000, building_total_area_sqft=1_000, post_date=date(2025, 6, 1)),
        HistoricalListing(area_name="Dubai Marina", price=None, building_total_area_sqft=None, post_date=None),
    ]

    context = build_market_context("Dubai Marina", listings)

    assert context["record_count"] == 3
    assert context["price_median"] == 1_250_000
    assert context["price_q1"] == 1_125_000
    assert context["price_q3"] == 1_375_000
    assert "price_per_sqft_min" not in context
    assert context["evidence_quality"] == "insufficient"
    assert context["period_start"] == date(2025, 1, 1)


def test_market_context_reports_matching_basis_without_estimating_values():
    context = build_market_context("Dubai Marina", [], ["area", "property_type", "beds"])

    assert context["matching_basis"] == ["area", "property_type", "beds"]
    assert context["record_count"] == 0
    assert context["price_median"] is None
    assert context["evidence_quality"] == "insufficient"


def test_market_context_filters_iqr_outliers_and_reports_quality():
    listings = [
        HistoricalListing(area_name="Dubai Marina", price=price, post_date=date(2025, 1, 1))
        for price in [1_000_000] * 20 + [99_000_000]
    ]

    context = build_market_context("Dubai Marina", listings)

    assert context["record_count"] == 21
    assert context["usable_record_count"] == 20
    assert context["price_median"] == 1_000_000
    assert context["evidence_quality"] == "strong"
