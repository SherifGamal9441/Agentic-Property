"""
Query Routing Node

Two-tier tool strategy to fetch relevant properties via the DLD MCP server:

  Tier 1 — Active tool:
      Current live listings. If it returns >= 1 property the pipeline proceeds
      with data_intent="recommend" -- properties are live and can be recommended.

  Tier 2 — Historical tool:
      Older DLD transactions. Used only when active returns nothing.
      Sets data_intent="insights_only" -- the comparison engine and answer
      generation nodes MUST NOT recommend these properties (may be sold/leased).
      They should derive market insights only: price ranges, area trends, etc.

Writes to state:
    retrieved_properties: list[dict]
    data_source: "active" | "historical"
    data_intent: "recommend" | "insights_only"
"""

import logging

from src.agents.state import AgentState
from src.mcp import (
    search_active_sync,
    search_historical_sync,
    convert_currency_sync,
)

logger = logging.getLogger(__name__)


# parsed_query keys match the MCP tool parameter names 1:1 (set by
# query_understanding LLM), so we pass them straight through — except
# property_price_minimum/property_price_maximum which may need currency conversion to AED.


def _convert_prices_to_aed(parsed_query: dict) -> tuple[dict, str, float | None]:
    """If user specified a non-AED currency, convert property_price_minimum/property_price_maximum to AED.

    Returns (updated_query, currency, exchange_rate).
    exchange_rate is None when no conversion was needed.
    """
    currency = parsed_query.pop("currency", None) or "AED"
    if currency.upper() == "AED":
        return parsed_query, "AED", None

    # Get a single rate (convert 1 unit of user currency → AED)
    rate_result = convert_currency_sync(currency, "AED", 1.0)
    if "error" in rate_result:
        logger.warning(
            "query_routing: currency conversion failed: %s — using raw values",
            rate_result.get("message"),
        )
        return parsed_query, currency, None

    rate = rate_result["rate"]
    logger.info(
        "query_routing: converting prices from %s to AED (rate=%s)", currency, rate
    )

    query = dict(parsed_query)
    for key in ("property_price_minimum", "property_price_maximum"):
        if key in query and query[key] is not None:
            query[key] = round(query[key] * rate, 2)

    return query, currency, rate


def _call_active_tool(parsed_query: dict) -> list[dict]:
    """Search active DLD listings via MCP server."""
    logger.info("_call_active_tool: searching active listings with %s", parsed_query)
    return search_active_sync(**parsed_query)


def _call_historical_tool(parsed_query: dict) -> list[dict]:
    """Search historical DLD transactions via MCP server."""
    logger.info("_call_historical_tool: searching historical with %s", parsed_query)
    return search_historical_sync(**parsed_query)


##node itself
def query_routing_node(state: AgentState) -> dict:
    """
    LangGraph node: fetch properties via active or historical tool.

    Strategy:
      1. Convert prices to AED if user specified a non-AED currency.
      2. Try active tool -> if results: data_source="active", data_intent="recommend"
      3. If active empty -> try historical tool -> data_source="historical", data_intent="insights_only"
      4. If both empty -> empty list, data_intent="insights_only" (nothing to work with)
    """
    parsed_query = dict(state.parsed_query)
    parsed_query, currency, exchange_rate = _convert_prices_to_aed(parsed_query)

    base_result = {
        "currency": currency,
        "exchange_rate": exchange_rate,
    }

    logger.info("query_routing: trying active data")
    active_results = _call_active_tool(parsed_query)

    if active_results:
        logger.info(
            "query_routing: active data returned %d properties -> route=recommend",
            len(active_results),
        )
        return {
            **base_result,
            "retrieved_properties": active_results,
            "data_source": "active",
            "data_intent": "recommend",
        }

    logger.info("query_routing: active data returned nothing, trying historical data")
    historical_results = _call_historical_tool(parsed_query)

    if historical_results:
        logger.info(
            "query_routing: historical data returned %d properties -> route=insights_only",
            len(historical_results),
        )
        return {
            **base_result,
            "retrieved_properties": historical_results,
            "data_source": "historical",
            "data_intent": "insights_only",
        }
    else:
        logger.warning(
            "query_routing: both tools returned nothing -- proceeding with web search"
        )
        return {
            **base_result,
            "retrieved_properties": [],
            "data_source": "historical",
            "data_intent": "insights_only",
        }


# ── Conditional edge router ───────────────────────────────────────────────────


def route_after_routing(state: AgentState) -> str:
    """After query_routing: go to comparison_engine if we have properties,
    otherwise fall back to web_search."""
    if not state.retrieved_properties:
        return "web_search"
    return "comparison_engine"
