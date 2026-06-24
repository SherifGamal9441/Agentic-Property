from pydantic import BaseModel, Field
from typing import Optional


class SearchHistoricalParams(BaseModel):
    area_name: Optional[str] = None
    address: Optional[str] = None
    building_name: Optional[str] = None
    type: Optional[str] = None
    furnishing: Optional[str] = None
    completion_status: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    beds_min: Optional[int] = None
    beds_max: Optional[int] = None
    baths_min: Optional[int] = None
    baths_max: Optional[int] = None
    year_of_completion_min: Optional[int] = None
    year_of_completion_max: Optional[int] = None
    total_parking_spaces_min: Optional[int] = None
    total_parking_spaces_max: Optional[int] = None
    total_floors_min: Optional[int] = None
    total_floors_max: Optional[int] = None
    total_building_area_sqft_min: Optional[float] = None
    total_building_area_sqft_max: Optional[float] = None
    post_date_min: Optional[str] = None
    post_date_max: Optional[str] = None
    limit: int = 20


class SearchActiveParams(BaseModel):
    area_name: Optional[str] = None
    address: Optional[str] = None
    building_name: Optional[str] = None
    type: Optional[str] = None
    furnishing: Optional[str] = None
    completion_status: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    beds_min: Optional[int] = None
    beds_max: Optional[int] = None
    baths_min: Optional[int] = None
    baths_max: Optional[int] = None
    year_of_completion_min: Optional[int] = None
    year_of_completion_max: Optional[int] = None
    total_parking_spaces_min: Optional[int] = None
    total_parking_spaces_max: Optional[int] = None
    total_floors_min: Optional[int] = None
    total_floors_max: Optional[int] = None
    total_building_area_sqft_min: Optional[float] = None
    total_building_area_sqft_max: Optional[float] = None
    limit: int = 20


class CompareListingsParams(BaseModel):
    area_name: Optional[str] = None
    type: Optional[str] = None
    furnishing: Optional[str] = None
    beds_min: Optional[int] = None
    beds_max: Optional[int] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    limit: int = 20


class ConvertCurrencyParams(BaseModel):
    from_currency: str
    to_currency: str
    amount: float
