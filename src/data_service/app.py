# data-service/main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import date, datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict, validator

from .database import get_db
from .db_tables import HistoricalListing, ActiveListing

# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class BaseSearchRequest(BaseModel):
    area_name: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    beds_min: Optional[int] = None
    beds_max: Optional[int] = None
    baths_min: Optional[int] = None
    baths_max: Optional[int] = None
    type: Optional[str] = None
    furnishing: Optional[str] = None
    completion_status: Optional[str] = None
    building_name: Optional[str] = None
    address: Optional[str] = None
    year_of_completion_min: Optional[int] = None
    year_of_completion_max: Optional[int] = None
    total_parking_spaces_min: Optional[int] = None
    total_parking_spaces_max: Optional[int] = None
    total_floors_min: Optional[int] = None
    total_floors_max: Optional[int] = None
    total_building_area_sqft_min: Optional[float] = None
    total_building_area_sqft_max: Optional[float] = None
    limit: int = Field(default=20, ge=1, le=100)

class HistoricalSearchRequest(BaseSearchRequest):
    post_date_min: Optional[date] = None
    post_date_max: Optional[date] = None

    @validator('post_date_min', 'post_date_max', pre=True)
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD.")
        return v

class ActiveSearchRequest(BaseSearchRequest):
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
    total_parking_spaces: Optional[int]
    total_floors: Optional[int]
    total_building_area_sqft: Optional[float]
    elevators: Optional[int]
    area_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    link: Optional[str]

class SearchResponse(BaseModel):
    total_matches: int
    returned_count: int
    listings: List[ListingResponse]

# ---------------------------------------------------------------------------
# Helper: build query filters
# ---------------------------------------------------------------------------

def apply_filters(query, model, filters: BaseSearchRequest):
    """
    Apply all non-null filters from the request to the SQLAlchemy query.
    """
    # Equality filters (string fields) — exact match
    eq_fields = [
        'area_name', 'type', 'furnishing', 'completion_status',
    ]
    for field in eq_fields:
        value = getattr(filters, field, None)
        if value is not None:
            query = query.filter(getattr(model, field) == value)

    # Partial case-insensitive match for address and building name
    for field in ('address', 'building_name'):
        value = getattr(filters, field, None)
        if value is not None:
            query = query.filter(getattr(model, field).ilike(f'%{value}%'))

    # Range filters (numeric)
    range_fields = [
        ('price', 'price_min', 'price_max'),
        ('beds', 'beds_min', 'beds_max'),
        ('baths', 'baths_min', 'baths_max'),
        ('year_of_completion', 'year_of_completion_min', 'year_of_completion_max'),
        ('total_parking_spaces', 'total_parking_spaces_min', 'total_parking_spaces_max'),
        ('total_floors', 'total_floors_min', 'total_floors_max'),
        ('total_building_area_sqft', 'total_building_area_sqft_min', 'total_building_area_sqft_max'),
    ]
    for col, min_attr, max_attr in range_fields:
        min_val = getattr(filters, min_attr, None)
        max_val = getattr(filters, max_attr, None)
        if min_val is not None:
            query = query.filter(getattr(model, col) >= min_val)
        if max_val is not None:
            query = query.filter(getattr(model, col) <= max_val)

    # Date range for historical (handled separately)
    if hasattr(filters, 'post_date_min') and filters.post_date_min is not None:
        query = query.filter(model.post_date >= filters.post_date_min)
    if hasattr(filters, 'post_date_max') and filters.post_date_max is not None:
        query = query.filter(model.post_date <= filters.post_date_max)

    return query

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Dubai Real Estate Data Service")

@app.get("/health")
def health_check():
    return {"status": "ok"}

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