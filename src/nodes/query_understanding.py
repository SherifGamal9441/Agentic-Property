"""
Query Understanding Node

Two responsibilities in a single LLM call:
  1. Parse the user query into a structured dict (location, budget, property type, etc.)
  2. Decide which path the graph takes next:
       "query_routing" → user wants specific property recommendations or comparisons
       "web_search"    → user has a general question about Dubai real estate

Route decision rule:
  → query_routing  if: user asks for a specific property, wants to compare options,
                       or needs a recommendation matching stated criteria
  → web_search     if: user asks about market trends, area information, general
                       advice, investment landscape, or anything informational
                       that doesn't require fetching specific listings

Writes to state:
    parsed_query: dict
    route: "query_routing" | "web_search"
"""

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.state import AgentState
from src.llm.factory import get_llm

logger = logging.getLogger(__name__)

# ── Prompt ────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a query parser for a Dubai real estate assistant.

Your job is to do two things from the user's query:

1. PARSE: Extract structured intent into a JSON object.
   Only include keys that are explicitly or strongly implied by the query.
   Never invent values. Use null for anything not mentioned.
   Fix any typos or misspellings in the user's query before extracting.
   For area_name, building_name, and address, correct typos to the most
   likely real Dubai location/building name (e.g "Dubai Mrina" → "Dubai Marina",
   "Jumeriah" → "Jumeirah", "buisness bay" → "Business Bay").
   For type, furnishing, and completion_status, correct to the exact enum
   values listed below.

   Possible keys:
    area_name: Optional[str] = None - e.g "Dubai Marina"
    address: Optional[str] = None - e.g "123 Main St"
    building_name: Optional[str] = None - e.g "Burj Khalifa"
    type: Optional[str] = None - e.g "apartment" | "villa" | "townhouse" | "studio" | "penthouse" | "office" | "retail"
    furnishing: Optional[str] = None - e.g "furnished" | "unfurnished"
    completion_status: Optional[str] = None - e.g "off-plan" | "ready"
    price_min: Optional[float] = None - minimum price in the user's currency
    price_max: Optional[float] = None - maximum price in the user's currency
    currency: Optional[str] = None - currency code the user mentioned (e.g "USD", "EUR", "GBP"). Omit or null if user says AED or doesn't specify.
    beds_min: Optional[int] = None - minimum number of bedrooms
    beds_max: Optional[int] = None - maximum number of bedrooms
    baths_min: Optional[int] = None - minimum number of bathrooms
    baths_max: Optional[int] = None - maximum number of bathrooms
    year_of_completion_min: Optional[int] = None - minimum year of completion
    year_of_completion_max: Optional[int] = None - maximum year of completion
    total_parking_spaces_min: Optional[int] = None - minimum number of parking spaces
    total_parking_spaces_max: Optional[int] = None - maximum number of parking spaces
    total_floors_min: Optional[int] = None - minimum number of floors
    total_floors_max: Optional[int] = None - maximum number of floors
    total_building_area_sqft_min: Optional[float] = None - minimum total building area in sqft
    total_building_area_sqft_max: Optional[float] = None - maximum total building area in sqft
    post_date_min: Optional[str] = None - minimum post date
    post_date_max: Optional[str] = None - maximum post date


2. ROUTE: Decide which path to take.
     "query_routing"  → user wants specific property results, recommendations, or comparisons
     "web_search"     → user is asking a general question (market trends, area overview,
                        investment advice, mortgage info, etc.)

Return ONLY valid JSON — no prose, no markdown fences:
{
  "parsed_query": { ... },
  "route": "query_routing" | "web_search",
  "route_reason": "<one sentence explaining the routing decision>"
}
"""

_USER_PROMPT_TEMPLATE = "Parse and route this query: {query}"


# ── Node function ─────────────────────────────────────────────────────────────


def query_understanding_node(state: AgentState) -> dict:
    """
    LangGraph node: parse the user query and decide the routing path.

    Args:
        state: Current AgentState. Reads `query`.

    Returns:
        Partial state dict with `parsed_query` and `route` populated.
    """
    logger.info("query_understanding: parsing query and deciding route")

    llm = get_llm(streaming=False)

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=_USER_PROMPT_TEMPLATE.format(query=state.query)),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            logger.error("query_understanding: could not parse LLM response:\n%s", raw)
            # Fail safe: treat as a web_search query (less risky default)
            result = {
                "parsed_query": {},
                "route": "web_search",
                "route_reason": "parse failure fallback",
            }

    parsed_query: dict = result.get("parsed_query", {})
    route: str = result.get("route", "web_search")

    # ── Vague query guard: if user wants properties but gave < 3 filters,
    #    ask for more info instead of running a useless search.
    _SEARCH_FILTERS = {
        "area_name", "type", "beds_min", "beds_max", "price_min",
        "price_max", "furnishing", "completion_status",
        "baths_min", "baths_max", "building_name", "address",
        "year_of_completion_min", "year_of_completion_max",
        "total_parking_spaces_min", "total_parking_spaces_max",
        "total_floors_min", "total_floors_max",
        "total_building_area_sqft_min", "total_building_area_sqft_max",
    }
    _filter_count = sum(1 for k in _SEARCH_FILTERS if parsed_query.get(k) is not None)

    if _filter_count < 3 and route == "query_routing":
        logger.info(
            "query_understanding: too vague (%d filters) — asking for more info",
            _filter_count,
        )
        return {
            "parsed_query": parsed_query,
            "route": "end",
            "final_answer": (
                "I can help you find property in Dubai! "
                "To narrow down the search, tell me a bit more:\n"
                "  - Which area? (e.g. Dubai Marina, Downtown, JVC, Palm Jumeirah)\n"
                "  - How many bedrooms?\n"
                "  - What's your budget?\n"
                "  - Property type? (apartment, villa, townhouse, studio)\n"
                "  - Furnishing? (furnished, unfurnished)"
            ),
        }

    logger.info(
        "query_understanding: route=%s | parsed=%s | reason=%s",
        route,
        list(parsed_query.keys()),
        result.get("route_reason", ""),
    )

    return {
        "parsed_query": parsed_query,
        "route": route,
    }


# ── Conditional edge router ───────────────────────────────────────────────────


def route_after_understanding(state: AgentState) -> str:
    """
    Called by LangGraph after query_understanding_node.

    Returns:
        "query_routing" — fetch properties and compare
        "web_search"    — answer a general question via web search
        "end"           — too vague, ask user for more info
    """
    return state.route or "web_search"
