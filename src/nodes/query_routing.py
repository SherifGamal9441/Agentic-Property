"""
Query Routing Node

Property runs search only the active-listing data snapshot. Historical records
remain an explicitly separate context endpoint and are never fallback inventory.

Writes to state:
    retrieved_properties: list[dict]
    data_source: "active" | "historical"
    data_intent: "recommend" | "insights_only"
"""

import logging
import json

from src.agents.state import AgentState
from src.mcp import (
    search_active_sync,
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


def _call_active_tool(parsed_query: dict) -> tuple[list[dict], str | None]:
    """Search active DLD listings via MCP server.
    Returns (listings, error_msg). error_msg is None on success.
    Empty list + no error = query matched 0 rows (not a failure)."""
    logger.info("_call_active_tool: searching active listings with %s", parsed_query)
    try:
        return search_active_sync(**parsed_query), None
    except (RuntimeError, json.JSONDecodeError) as e:
        logger.error("_call_active_tool: MCP failure: %s", e)
        return [], f"MCP active search failed: {e}"


##node itself
def query_routing_node(state: AgentState) -> dict:
    """
    LangGraph node: fetch properties via active or historical tool.
    Search the active data snapshot once. Empty results stay empty so the API
    can offer explicit, buyer-approved relaxation options.
    """
    parsed_query = dict(state.parsed_query)
    parsed_query, currency, exchange_rate = _convert_prices_to_aed(parsed_query)

    base_result = {
        "currency": currency,
        "exchange_rate": exchange_rate,
    }

    logger.info("query_routing: trying active data")
    active_results, active_error = _call_active_tool(parsed_query)

    if active_error:
        raise RuntimeError("The listing data snapshot is temporarily unavailable.")
    logger.info("query_routing: active snapshot returned %d candidates", len(active_results))
    return {
        **base_result,
        "retrieved_properties": active_results,
        "data_source": "active",
        "data_intent": "recommend",
    }


# ── Conditional edge router ───────────────────────────────────────────────────


def route_after_routing(state: AgentState) -> str:
    """After query_routing: go to comparison_engine if we have properties,
    otherwise fall back to web_search."""
    if not state.retrieved_properties:
        return "answer_generation"
    return "comparison_engine"
