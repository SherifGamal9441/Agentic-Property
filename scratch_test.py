from langchain_core.utils.json import parse_json_markdown, parse_partial_json
import json

raw = """
{
  "parsed_query": {
    "area_name": "Al Satwa, Jumeirah Garden City",
    "type": "apartment",
    "price_min": 1000000,
    "price_max": 2000000,
    "currency": null,
    "beds_min": 1,
    "beds_max": 1,
    "baths_min": 2,
    "baths_max": 2
  },
  "route": "query_routing
"""
try:
    print(parse_partial_json(raw))
except Exception as e:
    print("Error:", e)
