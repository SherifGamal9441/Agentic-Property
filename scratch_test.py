from langchain_core.utils.json import parse_json_markdown, parse_partial_json
import json

raw = """
{
  "parsed_query": {
    "area_name": "Al Satwa, Jumeirah Garden City",
    "type": "apartment",
    "property_price_minimum": 1000000,
    "property_price_maximum": 2000000,
    "currency": null,
    "property_beds_minimum": 1,
    "property_beds_maximum": 1,
    "property_bathrooms_minimum": 2,
    "property_bathrooms_maximum": 2
  },
  "route": "query_routing
"""
try:
    print(parse_partial_json(raw))
except Exception as e:
    print("Error:", e)
