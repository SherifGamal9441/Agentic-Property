"""
Query Routing Node

Two-tier tool strategy to fetch relevant properties:

  Tier 1 — Cached tool (teammates will implement):
      Fast, current listings. If it returns ≥ 1 property the pipeline proceeds
      with data_intent="recommend" — properties are live and can be recommended.

  Tier 2 — Historical tool (teammates will implement):
      Slower, older dataset. Used only when cached returns nothing.
      Sets data_intent="insights_only" — the comparison engine and answer
      generation nodes MUST NOT recommend these properties (may be sold/leased).
      They should derive market insights only: price ranges, area trends, etc.

Tool stubs:
    Both tool functions are stubs that return [] until teammates wire in the
    real implementations. The pipeline runs end-to-end with empty results —
    answer_generation will produce a "no properties found" response gracefully.

Writes to state:
    retrieved_properties: list[dict]
    data_source: "cached" | "historical"
    data_intent: "recommend" | "insights_only"
"""

import logging

from src.agents.state import AgentState

logger = logging.getLogger(__name__)


# ── Tool stubs (teammates: replace these bodies) ──────────────────────────────

def _call_cached_tool(parsed_query: dict) -> list[dict]:
    """
    STUB — Cached property search tool.

    This function will be replaced by the teammate responsible for the
    data ingestion / search layer (P1). It should query the live property
    cache (e.g. Bayut cache, vector DB, or SQL filter) and return a list
    of property dicts matching the parsed_query criteria.

    Expected return format per property:
        {
            "id": str,
            "title": str,
            "price": int,          # in AED
            "area_sqm": float,
            "location": str,
            "bedrooms": int,
            "amenities": list[str],
        }

    Returns:
        list[dict] — matching properties, or [] if none found.
    """
    # TODO: wire in real cached search tool
    logger.debug("_call_cached_tool: stub called with query=%s", parsed_query)
    return []


def _call_historical_tool(parsed_query: dict) -> list[dict]:
    """
    STUB — Historical property dataset tool.

    This function will be replaced by the teammate responsible for the
    data ingestion layer (P1). It should query the historical dataset
    (e.g. DLD CSV, sales/rentals CSV) and return older property records
    matching the parsed_query criteria.

    ⚠️  Properties returned here may already be sold or leased.
        The data_intent field will be set to "insights_only" so that
        downstream nodes know NOT to recommend these specific properties.

    Expected return format: same as _call_cached_tool.

    Returns:
        list[dict] — historical records, or [] if none found.
    """
    # TODO: wire in real historical dataset tool
    logger.debug("_call_historical_tool: stub called with query=%s", parsed_query)
    return []


# ── Node function ─────────────────────────────────────────────────────────────

def query_routing_node(state: AgentState) -> dict:
    """
    LangGraph node: fetch properties via cached or historical tool.

    Strategy:
      1. Try cached tool → if results: data_source="cached", data_intent="recommend"
      2. If cached empty → try historical tool → data_source="historical", data_intent="insights_only"
      3. If both empty → empty list, data_intent="insights_only" (nothing to work with)

    The comparison_engine node reads data_intent to adjust its prompt:
      - "recommend"     → score and rank, identify best match
      - "insights_only" → derive market trends only, do NOT recommend specific properties

    Args:
        state: Current AgentState. Reads `parsed_query`.

    Returns:
        Partial state dict with `retrieved_properties`, `data_source`, `data_intent`.
    """
    logger.info("query_routing: trying cached tool")
    cached_results = _call_cached_tool(state.parsed_query)

    if cached_results:
        logger.info("query_routing: cached tool returned %d properties → route=recommend", len(cached_results))
        return {
            "retrieved_properties": cached_results,
            "data_source": "cached",
            "data_intent": "recommend",
        }

    logger.info("query_routing: cached tool returned nothing, trying historical tool")
    historical_results = _call_historical_tool(state.parsed_query)

    if historical_results:
        logger.info(
            "query_routing: historical tool returned %d properties → route=insights_only",
            len(historical_results),
        )
    else:
        logger.warning("query_routing: both tools returned nothing — proceeding with empty results")

    return {
        "retrieved_properties": historical_results,
        "data_source": "historical",
        "data_intent": "insights_only",
    }
