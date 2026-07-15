"""Validated public buyer-brief contract and deterministic field translation."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


Priority = Literal["must_have", "nice_to_have", "deal_breaker"]
Operator = Literal["eq", "contains", "gte", "lte", "not_eq"]
SupportedField = Literal[
    "area",
    "price",
    "property_type",
    "bedrooms",
    "bathrooms",
    "furnishing",
    "completion_status",
    "building_name",
    "completion_year",
]


class Criterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=160)
    priority: Priority
    field: SupportedField | None = None
    operator: Operator | None = None
    value: str | int | float | bool | None = None
    verifiable: bool = True

    @model_validator(mode="after")
    def validate_evidence_contract(self) -> "Criterion":
        parts = (self.field, self.operator, self.value)
        if self.verifiable and any(part is None for part in parts):
            raise ValueError("Verifiable criteria require field, operator, and value.")
        if not self.verifiable and any(part is not None for part in parts):
            raise ValueError("Unverifiable criteria cannot claim a structured dataset check.")
        return self


class BuyerBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[1] = 1
    mode: Literal["property_search", "web_research"] = "property_search"
    original_query: str = Field(min_length=1, max_length=1_000)
    currency: str = Field(default="AED", min_length=3, max_length=3)
    criteria: list[Criterion] = Field(default_factory=list, max_length=30)


FIELD_KEYS: dict[str, tuple[str, ...]] = {
    "area": ("area_name", "area", "location"),
    "price": ("price",),
    "property_type": ("type", "property_type"),
    "bedrooms": ("beds", "bedrooms"),
    "bathrooms": ("baths", "bathrooms"),
    "furnishing": ("furnishing",),
    "completion_status": ("completion_status",),
    "building_name": ("building_name",),
    "completion_year": ("year_of_completion", "completion_year"),
}


def property_value(property_data: dict[str, Any], field: str) -> Any:
    for key in FIELD_KEYS[field]:
        if key in property_data and property_data[key] is not None:
            return property_data[key]
    return None


def brief_to_filters(brief: BuyerBrief) -> dict[str, Any]:
    """Translate only confirmed, supported hard criteria into MCP filters."""
    filters: dict[str, Any] = {"limit": 20}
    if brief.currency != "AED":
        filters["currency"] = brief.currency
    mappings = {
        ("area", "contains"): "area_name",
        ("area", "eq"): "area_name",
        ("price", "gte"): "property_price_minimum",
        ("price", "lte"): "property_price_maximum",
        ("property_type", "contains"): "type",
        ("property_type", "eq"): "type",
        ("bedrooms", "gte"): "property_beds_minimum",
        ("bedrooms", "lte"): "property_beds_maximum",
        ("bedrooms", "eq"): ("property_beds_minimum", "property_beds_maximum"),
        ("bathrooms", "gte"): "property_bathrooms_minimum",
        ("bathrooms", "lte"): "property_bathrooms_maximum",
        ("bathrooms", "eq"): ("property_bathrooms_minimum", "property_bathrooms_maximum"),
        ("furnishing", "eq"): "furnishing",
        ("completion_status", "eq"): "completion_status",
        ("building_name", "contains"): "building_name",
        ("building_name", "eq"): "building_name",
        ("completion_year", "gte"): "year_of_completion_minimum",
        ("completion_year", "lte"): "year_of_completion_maximum",
        ("completion_year", "eq"): ("year_of_completion_minimum", "year_of_completion_maximum"),
    }
    for criterion in brief.criteria:
        if not criterion.verifiable or criterion.priority == "nice_to_have":
            continue
        target = mappings.get((criterion.field, criterion.operator))
        if target is None or criterion.operator == "not_eq":
            continue
        if isinstance(target, tuple):
            for key in target:
                filters[key] = criterion.value
        else:
            filters[target] = criterion.value
    return filters
