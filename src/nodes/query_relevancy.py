"""
Query Relevancy Node

First gate in the pipeline. Checks two hard rules before any other work is done:
  1. Is the question about Dubai? (not other cities or countries)
  2. Is the question about real estate / property topics?

If either rule fails the graph ends immediately — no further LLM calls.
The final_answer field carries a warm explanation so the API layer always
reads a single field regardless of which path ran.

Writes to state:
    is_relevant: bool
    final_answer: str | None   — set only when is_relevant=False
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
You are a query classifier for a Dubai real estate assistant.

You must evaluate every user query against exactly two rules:
  Rule 1 — Geography: The query must be about Dubai or areas within Dubai.
            Queries about other cities, countries, or unspecified locations fail this rule.
  Rule 2 — Topic:     The query must be about real estate or property.
            This includes: buying, renting, investing, prices, market trends, property types,
            locations within Dubai, mortgages, developers, and similar topics.
            Anything unrelated to real estate fails this rule.

Return ONLY valid JSON — no prose, no markdown fences:
{
  "relevant": true | false,
  "failed_rule": null | "geography" | "topic" | "both",
  "reason": "<one short sentence explaining why it passed or failed>"
}
"""

_USER_PROMPT_TEMPLATE = "Classify this query: {query}"

# ── Rejection message builder ─────────────────────────────────────────────────

_SCOPE_LIST = (
    "Here's what I *can* help you with:\n"
    "• Finding apartments, villas, or townhouses for sale or rent in Dubai\n"
    "• Comparing properties across different Dubai neighbourhoods\n"
    "• Market insights and price trends for Dubai real estate\n"
    "• Advice on buying, renting, or investing in Dubai property\n\n"
    "Feel free to ask about any of the above!"
)

_OPENINGS = {
    "geography": (
        "I can only help with property searches and real estate questions "
        "specifically in Dubai.\n\n"
        "Your question seems to be about a location outside Dubai — "
        "I'm not able to assist with that."
    ),
    "topic": (
        "I'm a specialised Dubai real estate assistant — I can only help with "
        "property-related questions.\n\n"
        "Your question appears to be about something outside my area of expertise."
    ),
    "both": (
        "I'm a specialised Dubai real estate assistant. Your question is outside "
        "what I can help with — it's neither about Dubai nor about property topics."
    ),
}


def _rejection_msg(failed_rule: str) -> str:
    opening = _OPENINGS.get(failed_rule, _OPENINGS["both"])
    return f"{opening}\n\n{_SCOPE_LIST}"


# ── Node function ─────────────────────────────────────────────────────────────

def query_relevancy_node(state: AgentState) -> dict:
    """
    LangGraph node: classify the user query before any downstream work runs.

    Args:
        state: Current AgentState. Reads `query`.

    Returns:
        Partial state dict.
        - If relevant: {"is_relevant": True}
        - If not: {"is_relevant": False, "final_answer": <rejection message>}
    """
    logger.info("query_relevancy: classifying query")

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
            # Cannot parse — fail safe: let the query through rather than block valid users
            logger.warning("query_relevancy: could not parse LLM response, defaulting to relevant")
            return {"is_relevant": True}

    is_relevant: bool = result.get("relevant", True)
    failed_rule: str = result.get("failed_rule") or "both"

    if is_relevant:
        logger.info("query_relevancy: query accepted")
        return {"is_relevant": True}

    rejection = _rejection_msg(failed_rule)
    logger.info("query_relevancy: query rejected (rule=%s, reason=%s)", failed_rule, result.get("reason"))

    return {
        "is_relevant": False,
        "final_answer": rejection,
    }


# ── Conditional edge router ───────────────────────────────────────────────────

def route_after_relevancy(state: AgentState) -> str:
    """
    Called by LangGraph after query_relevancy_node.

    Returns:
        "query_understanding" — query is in scope, proceed
        "end"                 — query is out of scope, stop here
    """
    if state.is_relevant:
        return "query_understanding"
    return "end"
