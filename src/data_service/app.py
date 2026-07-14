# src/data_service/app.py
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, validator
from src.mcp.schemas import BasePropertyFilters, HistoricalFilters

from .database import get_database_status, get_db
from .db_tables import HistoricalListing, ActiveListing

# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class HistoricalSearchRequest(HistoricalFilters):
    @validator('post_date_minimum', 'post_date_maximum', pre=True)
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
        ('total_parking_spaces', 'parking_spaces_minimum', 'parking_spaces_maximum'),
        ('total_floors', 'total_floors_minimum', 'total_floors_maximum'),
        ('total_building_area_sqft', 'total_building_area_sqft_minimum', 'total_building_area_sqft_maximum'),
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
def health_check():
    return {"status": "ok", **get_database_status()}

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
