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
from src.area_matcher import fuzzy_match_area
from src.llm.factory import get_llm
from src.utils import parse_llm_json

logger = logging.getLogger(__name__)

# ── Prompts ───────────────────────────────────────────────────────────────────

from pathlib import Path as _Path
import yaml as _yaml

_PROMPTS_DIR = _Path(__file__).parent.parent / "prompts"

_PROMPTS = _yaml.safe_load((_PROMPTS_DIR / "query_understanding.yaml").read_text(encoding="utf-8"))
_SYSTEM_PROMPT = _PROMPTS["system_prompt"]
_USER_PROMPT_TEMPLATE = _PROMPTS["user_prompt_template"]


# ── Area name normalizer ──────────────────────────────────────────────────────

# Maps any LLM-produced area name variant → canonical lowercase DB value.
# Order matters: more specific entries must come before shorter prefixes.
_AREA_ALIAS_MAP: dict[str, str] = {
    # Dubai prefix stripping
    "dubai marina": "marina",
    "dubai hills estate": "dubai hills estate",  # keep as-is (already correct)
    "dubai hills": "dubai hills estate",
    "dubai silicon oasis": "silicon oasis",
    "dubai sports city": "sports city",
    "dubai production city": "production city",
    "dubai investment park": "dubai investment park",
    "dubai creek harbour": "dubai creek harbour",
    "dubai south": "dubai south",
    # Abbreviation expansions (in case prompt misses them)
    "jlt": "jumeirah lake towers",
    "jbr": "jumeirah beach residence",
    "jvc": "jumeirah village circle",
    "jvt": "jumeirah village triangle",
    # Common variants
    "downtown dubai": "downtown",
    "downtown, dubai": "downtown",
    "palm jumeirah, dubai": "palm jumeirah",
    "business bay, dubai": "business bay",
    # DAMAC Hills sub-community
    "damac hills estate": "damac hills",
    "damac hills 2": "damac hills",          # building, not area
    "arabian ranches 2": "arabian ranches",  # sub-community
    "arabian ranches 3": "arabian ranches",
    # City-level values that should be null
    "dubai": None,
    "dubai, uae": None,
    "uae": None,
}


def _normalize_parsed_query(parsed_query: dict) -> dict:
    """
    Apply deterministic post-processing fixes to the LLM-produced parsed_query:

    1. area_name  — lowercase + alias map (strips "Dubai " prefix variants, etc.)
    2. type       — collapse "studio apartment" → "studio"
    3. currency   — uppercase; drop if AED (it's the default)

    Returns a new dict (does not mutate the input).
    """
    if not isinstance(parsed_query, dict):
        return {}

    pq = dict(parsed_query)

    # ── 1. area_name normalisation ────────────────────────────────────────────
    area = pq.get("area_name")
    if isinstance(area, str):
        area_lower = area.strip().lower()

        # City-level values → null (no specific area)
        if area_lower in ("dubai", "dubai, uae", "uae"):
            pq["area_name"] = None
            logger.debug("normalize: area_name %r → None (city-level)", area)
        else:
            # Fuzzy match against canonical CSV area names, then apply alias map
            matched = fuzzy_match_area(area)
            if matched is not None:
                pq["area_name"] = _AREA_ALIAS_MAP.get(matched, matched)
            else:
                pq["area_name"] = None
            logger.debug(
                "normalize: area_name %r → %r", area, pq["area_name"]
            )

    # ── 2. type normalisation ─────────────────────────────────────────────────
    prop_type = pq.get("type")
    if isinstance(prop_type, str):
        t = prop_type.strip().lower()
        if t == "studio apartment":
            pq["type"] = "studio"
        else:
            pq["type"] = t

    # ── 3. currency normalisation ─────────────────────────────────────────────
    currency = pq.get("currency")
    if isinstance(currency, str):
        currency_upper = currency.strip().upper()
        if currency_upper == "AED":
            pq["currency"] = None   # AED is implicit; drop to avoid confusion
        else:
            pq["currency"] = currency_upper

    return pq


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
        HumanMessage(content=_USER_PROMPT_TEMPLATE.format(
            query=state.query,
            conversation_context=state.conversation_context,
        )),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    # Qwen thinking models may wrap output in <think>...</think> tags;
    # strip them so the JSON parser only sees the actual content.
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    # If content is empty (thinking model swallowed output), retry once.
    if not raw:
        logger.warning("query_understanding: empty response, retrying once")
        response = llm.invoke(messages)
        raw = response.content.strip()
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    try:
        result = parse_llm_json(raw)
    except json.JSONDecodeError:
        logger.error("query_understanding: could not parse LLM response:\n%s", raw)
        # Fail safe: treat as a web_search query (less risky default)
        result = {
            "parsed_query": {},
            "route": "web_search",
            "route_reason": "parse failure fallback",
        }

    parsed_query: dict = result.get("parsed_query") or {}
    route: str = result.get("route") or "web_search"

    # Apply deterministic post-processing to fix known LLM inconsistencies
    parsed_query = _normalize_parsed_query(parsed_query)

    logger.info(
        "query_understanding: route=%s | parsed=%s | reason=%s",
        route,
        list(parsed_query.keys()) if isinstance(parsed_query, dict) else [],
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
    """
    return state.route or "web_search"
