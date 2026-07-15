# src/data_service/app.py
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import date, datetime
from typing import Optional, List
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator
from src.mcp.schemas import BasePropertyFilters, HistoricalFilters

from .database import get_database_status, get_db
from .db_tables import HistoricalListing, ActiveListing

# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class HistoricalSearchRequest(HistoricalFilters):
    @field_validator('post_date_minimum', 'post_date_maximum', mode='before')
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD.")
        return v

class ActiveSearchRequest(BasePropertyFilters):
    # no post_date fields
    pass

# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class ListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    property_id: Optional[str]
    price: Optional[float]
    type: Optional[str]
    beds: Optional[int]
    baths: Optional[int]
    address: Optional[str]
    furnishing: Optional[str]
    completion_status: Optional[str]
    post_date: Optional[date]
    building_name: Optional[str]
    year_of_completion: Optional[int]
    building_total_parking_spaces: Optional[int] = Field(validation_alias=AliasChoices("building_total_parking_spaces", "total_parking_spaces"))
    building_floors: Optional[int] = Field(validation_alias=AliasChoices("building_floors", "total_floors"))
    building_total_area_sqft: Optional[float] = Field(validation_alias=AliasChoices("building_total_area_sqft", "total_building_area_sqft"))
    building_elevators: Optional[int] = Field(validation_alias=AliasChoices("building_elevators", "elevators"))
    area_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    link: Optional[str]

class SearchResponse(BaseModel):
    total_matches: int
    returned_count: int
    listings: List[ListingResponse]


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _iqr_prices(prices: list[float]) -> tuple[list[float], float | None, float | None]:
    q1 = _percentile(prices, 0.25)
    q3 = _percentile(prices, 0.75)
    if q1 is None or q3 is None:
        return prices, q1, q3
    spread = q3 - q1
    if spread == 0:
        filtered = [price for price in prices if price == q1]
    else:
        lower, upper = q1 - 1.5 * spread, q3 + 1.5 * spread
        filtered = [price for price in prices if lower <= price <= upper]
    return filtered, _percentile(filtered, 0.25), _percentile(filtered, 0.75)


def _evidence_quality(count: int) -> str:
    if count >= 20:
        return "strong"
    if count >= 5:
        return "limited"
    return "insufficient"


def build_market_context(area: str, listings: list[HistoricalListing], matching_basis: list[str] | None = None) -> dict:
    """Summarize transaction prices; building area is never treated as unit area."""
    prices = [float(listing.price) for listing in listings if listing.price is not None and listing.price >= 0]
    usable_prices, q1, q3 = _iqr_prices(prices)
    dates = [listing.post_date for listing in listings if listing.post_date is not None]
    property_types: dict[str, int] = {}
    bedrooms: dict[str, int] = {}
    for listing in listings:
        if listing.type:
            property_types[listing.type] = property_types.get(listing.type, 0) + 1
        if listing.beds is not None:
            key = str(listing.beds)
            bedrooms[key] = bedrooms.get(key, 0) + 1
    return {
        "area": area,
        "matching_basis": matching_basis or ["area"],
        "record_count": len(listings),
        "usable_record_count": len(usable_prices),
        "period_start": min(dates) if dates else None,
        "period_end": max(dates) if dates else None,
        "price_median": _percentile(usable_prices, 0.5),
        "price_q1": q1,
        "price_q3": q3,
        "evidence_quality": _evidence_quality(len(usable_prices)),
        "property_type_mix": property_types,
        "bedroom_mix": bedrooms,
    }

# ---------------------------------------------------------------------------
# Helper: build query filters
# ---------------------------------------------------------------------------

def apply_filters(query, model, filters: BasePropertyFilters):
    """
    Apply all non-null filters from the request to the SQLAlchemy query.
    """
    # Dump filters to a dictionary so we can normalize values safely
    filter_dict = filters.model_dump(exclude_none=True)
    is_active = (model.__tablename__ == "active_listings")

    # 1. Normalize completion_status based on model/table schema
    if "completion_status" in filter_dict:
        cs_val = str(filter_dict["completion_status"]).strip().lower()
        if is_active:
            # Active listings table expects: completed / under-construction
            if "ready" in cs_val or "completed" in cs_val:
                filter_dict["completion_status"] = "completed"
            elif "off-plan" in cs_val or "off plan" in cs_val or "under-construction" in cs_val:
                filter_dict["completion_status"] = "under-construction"
        else:
            # Historical listings table expects: Ready / Off-Plan
            if "completed" in cs_val or "ready" in cs_val:
                filter_dict["completion_status"] = "Ready"
            elif "under-construction" in cs_val or "off-plan" in cs_val or "off plan" in cs_val:
                filter_dict["completion_status"] = "Off-Plan"

    # 2. Normalize 'studio' property type
    # Studios are stored as 'Apartment' or 'Apartments' in CSVs with beds=0
    if "type" in filter_dict and str(filter_dict["type"]).strip().lower() == "studio":
        filter_dict["type"] = "Apartment"
        filter_dict["property_beds_minimum"] = 0
        filter_dict["property_beds_maximum"] = 0

    # String filters — use partial case-insensitive match (ilike)
    # This ensures "apartment" matches "Apartments" in the DB.
    # It also handles comma-separated lists from the LLM (e.g. "Al Satwa, Jumeirah")
    # by treating them as an OR condition.
    string_fields = [
        'area_name', 'type', 'furnishing', 'completion_status',
        'address', 'building_name'
    ]
    for field in string_fields:
        value = filter_dict.get(field)
        if value is not None:
            # Split by comma and strip whitespace for multiple values
            terms = [t.strip() for t in str(value).split(',')]
            if field == 'building_name':
                # Special handling for building_name: fall back to searching address as well
                conditions = []
                for term in terms:
                    if term:
                        conditions.append(model.building_name.ilike(f'%{term}%'))
                        conditions.append(model.address.ilike(f'%{term}%'))
            else:
                conditions = [getattr(model, field).ilike(f'%{term}%') for term in terms if term]
            
            if conditions:
                query = query.filter(or_(*conditions))

    # Range filters (numeric)
    range_fields = [
        ('price', 'property_price_minimum', 'property_price_maximum'),
        ('beds', 'property_beds_minimum', 'property_beds_maximum'),
        ('baths', 'property_bathrooms_minimum', 'property_bathrooms_maximum'),
        ('year_of_completion', 'year_of_completion_minimum', 'year_of_completion_maximum'),
    ]
    for col, min_attr, max_attr in range_fields:
        min_val = filter_dict.get(min_attr)
        max_val = filter_dict.get(max_attr)
        if min_val is not None:
            query = query.filter(getattr(model, col) >= min_val)
        if max_val is not None:
            query = query.filter(getattr(model, col) <= max_val)

    # Date range for historical (handled separately)
    post_date_minimum = filter_dict.get('post_date_minimum')
    post_date_maximum = filter_dict.get('post_date_maximum')
    if post_date_minimum is not None:
        query = query.filter(model.post_date >= post_date_minimum)
    if post_date_maximum is not None:
        query = query.filter(model.post_date <= post_date_maximum)

    return query

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Dubai Real Estate Data Service")

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    latest_active = db.query(ActiveListing.post_date).order_by(desc(ActiveListing.post_date).nulls_last()).first()
    active_snapshot_at = latest_active[0] if latest_active else None
    return {
        "status": "ok",
        **get_database_status(),
        "active_records": db.query(ActiveListing).count(),
        "historical_records": db.query(HistoricalListing).count(),
        "active_snapshot_at": active_snapshot_at,
    }


@app.get("/market-context")
def market_context(
    area: str = Query(min_length=1),
    property_type: str | None = Query(default=None, min_length=1),
    beds: int | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
):
    """Return only reported historical context for available comparable facts."""
    query = db.query(HistoricalListing).filter(HistoricalListing.area_name.ilike(f"%{area}%"))
    matching_basis = ["area"]
    if property_type:
        normalized_type = "Apartment" if property_type.strip().lower() == "apartments" else property_type.strip()
        query = query.filter(HistoricalListing.type.ilike(f"%{normalized_type}%"))
        matching_basis.append("property_type")
    if beds is not None:
        query = query.filter(HistoricalListing.beds == beds)
        matching_basis.append("beds")
    return build_market_context(area, query.all(), matching_basis)

@app.post("/search/historical", response_model=SearchResponse)
def search_historical(req: HistoricalSearchRequest, db: Session = Depends(get_db)):
    """
    Search historical listings with optional filters.
    """
    query = db.query(HistoricalListing)
    query = apply_filters(query, HistoricalListing, req)

    # Count total matches
    total = query.count()

    # Apply sorting and limit
    query = query.order_by(desc(HistoricalListing.post_date).nulls_last()).limit(req.limit)

    listings = query.all()

    # Convert to response model
    result_listings = [ListingResponse.model_validate(l) for l in listings]

    return SearchResponse(
        total_matches=total,
        returned_count=len(result_listings),
        listings=result_listings
    )

@app.post("/search/active", response_model=SearchResponse)
def search_active(req: ActiveSearchRequest, db: Session = Depends(get_db)):
    """
    Search active listings with optional filters.
    """
    query = db.query(ActiveListing)
    query = apply_filters(query, ActiveListing, req)

    total = query.count()

    query = query.order_by(desc(ActiveListing.post_date).nulls_last()).limit(req.limit)

    listings = query.all()

    result_listings = [ListingResponse.model_validate(l) for l in listings]

    return SearchResponse(
        total_matches=total,
        returned_count=len(result_listings),
        listings=result_listings
    )
