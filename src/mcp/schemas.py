from pydantic import BaseModel, Field
from typing import Optional

class BasePropertyFilters(BaseModel):
    area_name: Optional[str] = Field(
        default=None,
        description="Neighborhood or community name in Dubai (e.g. 'Marina', 'Downtown', 'JVC')."
    )
    address: Optional[str] = Field(
        default=None,
        description="Full or partial street address of the property."
    )
    building_name: Optional[str] = Field(
        default=None,
        description="Name of the specific building or tower (e.g. 'Burj Khalifa', 'Marina Gate')."
    )
    type: Optional[str] = Field(
        default=None,
        description=(
            "Property type. Use: 'Apartment', 'Villa', 'Townhouse', 'Penthouse', "
            "'Hotel Apartment', 'Residential Building', 'Residential Floor', "
            "'Residential Plot', 'Villa Compound'. "
        )
    )
    furnishing: Optional[str] = Field(
        default=None,
        description="Furnishing status. Exact values: 'Furnished' or 'Unfurnished'."
    )
    completion_status: Optional[str] = Field(
        default=None,
        description=(
            "Build status. Use 'Ready' for completed/built properties, "
            "or 'Off-Plan' for properties under construction. "
        )
    )
    property_price_minimum: Optional[float] = Field(
        default=None,
        description="Minimum listing price in AED (inclusive)."
    )
    property_price_maximum: Optional[float] = Field(
        default=None,
        description="Maximum listing price in AED (inclusive)."
    )
    property_beds_minimum: Optional[int] = Field(
        default=None,
        description="Minimum number of bedrooms (inclusive). Use 0 for Studio."
    )
    property_beds_maximum: Optional[int] = Field(
        default=None,
        description="Maximum number of bedrooms (inclusive)."
    )
    property_bathrooms_minimum: Optional[int] = Field(
        default=None,
        description="Minimum number of bathrooms (inclusive)."
    )
    property_bathrooms_maximum: Optional[int] = Field(
        default=None,
        description="Maximum number of bathrooms (inclusive)."
    )
    year_of_completion_minimum: Optional[int] = Field(
        default=None,
        description="Earliest year the building was or is expected to be completed (inclusive)."
    )
    year_of_completion_maximum: Optional[int] = Field(
        default=None,
        description="Latest year the building was or is expected to be completed (inclusive)."
    )
    parking_spaces_minimum: Optional[int] = Field(
        default=None,
        description="Minimum number of dedicated parking spaces (inclusive)."
    )
    parking_spaces_maximum: Optional[int] = Field(
        default=None,
        description="Maximum number of dedicated parking spaces (inclusive)."
    )
    total_floors_minimum: Optional[int] = Field(
        default=None,
        description="Minimum number of floors in the building (inclusive)."
    )
    total_floors_maximum: Optional[int] = Field(
        default=None,
        description="Maximum number of floors in the building (inclusive)."
    )
    total_building_area_sqft_minimum: Optional[float] = Field(
        default=None,
        description="Minimum total area of the property in square feet (inclusive)."
    )
    total_building_area_sqft_maximum: Optional[float] = Field(
        default=None,
        description="Maximum total area of the property in square feet (inclusive)."
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of results to return. Defaults to 20, max 100."
    )

class HistoricalFilters(BasePropertyFilters):
    post_date_minimum: Optional[str] = Field(
        default=None,
        description="Earliest transaction date to include, in ISO 8601 format (YYYY-MM-DD)."
    )
    post_date_maximum: Optional[str] = Field(
        default=None,
        description="Latest transaction date to include, in ISO 8601 format (YYYY-MM-DD)."
    )
