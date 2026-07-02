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
from src.utils import parse_llm_json

logger = logging.getLogger(__name__)

# ── Prompts ───────────────────────────────────────────────────────────────────

from src.prompts.loader import load_prompt

_PROMPTS = load_prompt("query_understanding.yaml")
_SYSTEM_PROMPT = _PROMPTS["system_prompt"]
_USER_PROMPT_TEMPLATE = _PROMPTS["user_prompt_template"]


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

    parsed_query: dict = result.get("parsed_query", {})
    route: str = result.get("route", "web_search")

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
    """
    return state.route or "web_search"
