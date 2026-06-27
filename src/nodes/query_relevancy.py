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

# ── Prompts ───────────────────────────────────────────────────────────────────

from src.prompts.loader import load_prompt

_PROMPTS = load_prompt("query_relevancy.yaml")
_SYSTEM_PROMPT = _PROMPTS["system_prompt"]
_USER_PROMPT_TEMPLATE = _PROMPTS["user_prompt_template"]
_SCOPE_LIST = _PROMPTS["scope_list"]
_OPENINGS = _PROMPTS["openings"]


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
