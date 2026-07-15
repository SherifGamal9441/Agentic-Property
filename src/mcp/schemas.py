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
        description=(
            "Name of the specific building or tower (e.g. 'Burj Khalifa', 'Marina Gate', "
            "'Palace Beach Residence Tower 2'). NOTE: some listings have the building name "
            "stored in the address field instead of building_name. The server automatically "
            "falls back to searching address if building_name yields no results."
        )
    )
    type: Optional[str] = Field(
        default=None,
        description=(
            "Property type. IMPORTANT: values differ by data source.\n"
            "- For ACTIVE listings: use 'Apartments' (plural is the only value in active data).\n"
            "- For HISTORICAL listings: use one of: 'Apartment', 'Villa', 'Townhouse', 'Penthouse', "
            "'Hotel Apartment', 'Residential Building', 'Residential Floor', "
            "'Residential Plot', 'Villa Compound'.\n"
            "Server uses partial case-insensitive matching, so 'apartment' will match both 'Apartments' and 'Apartment'."
        )
    )
    furnishing: Optional[str] = Field(
        default=None,
        description="Furnishing status. Exact values: 'Furnished' or 'Unfurnished'."
    )
    completion_status: Optional[str] = Field(
        default=None,
        description=(
            "Build status of the property. IMPORTANT: the expected value depends on the data source.\n"
            "- For ACTIVE listings: use 'completed' or 'under-construction'.\n"
            "- For HISTORICAL listings: use 'Ready' or 'Off-Plan'.\n"
            "Acceptable synonyms (server-side normalization will map them):\n"
            "  completed/built/ready → 'completed' (active) / 'Ready' (historical)\n"
            "  under-construction/off-plan/off plan → 'under-construction' (active) / 'Off-Plan' (historical)\n"
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
