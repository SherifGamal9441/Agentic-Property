"""
Comparison Engine Node

Receives the list of retrieved properties and the user's parsed requirements,
then uses the LLM to evaluate how well each property matches what the user wants.

Output written to state:
    comparison_result: {
        properties: [
            {
                id, title,
                fit_score: float (0.0–1.0),
                matched_criteria: list[str],
                unmatched_criteria: list[str],
                price_assessment: "below_market" | "fair" | "above_market"
            }
        ]
    }
"""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.state import AgentState
from src.llm.factory import get_llm
from src.utils import parse_llm_json

logger = logging.getLogger(__name__)

# ── Prompt templates ──────────────────────────────────────────────────────────

_SYSTEM_PROMPT_RECOMMEND = """\
You are an expert real estate comparison assistant specialising in UAE property.
Your job is to evaluate how well each retrieved property matches the user's requirements.

Rules:
- Be objective and data-driven. Only reference criteria explicitly stated in the requirements.
- fit_score: 0.0 = no match at all, 1.0 = perfect match on every criterion.
- price_assessment: compare the property's price to typical market rates for its type/location.
- Return ONLY valid JSON — no prose, no markdown fences, no extra keys.
"""

_SYSTEM_PROMPT_INSIGHTS = """\
You are an expert real estate comparison assistant specialising in UAE property.
You are evaluating HISTORICAL data. These properties may already be sold.
Your job is to evaluate them to derive market insights, not to recommend them as active listings.

Rules:
- Be objective and data-driven. Only reference criteria explicitly stated in the requirements.
- fit_score: 0.0 = no match at all, 1.0 = perfect match on every criterion.
- price_assessment: compare the property's price to typical market rates for its type/location.
- Return ONLY valid JSON — no prose, no markdown fences, no extra keys.
"""

_USER_PROMPT_TEMPLATE = """\
User requirements:
{parsed_query}

Retrieved properties:
{retrieved_properties}

For EACH property, produce an entry with exactly these fields:
  - id              (string)
  - title           (string)
  - fit_score       (float, 0.0 to 1.0)
  - matched_criteria    (array of strings — which user requirements this property satisfies)
  - unmatched_criteria  (array of strings — which user requirements this property does NOT satisfy)
  - price_assessment    ("below_market" | "fair" | "above_market")

Return a JSON object in this exact shape:
{{
  "properties": [ ... ]
}}
"""


# ── Node function ─────────────────────────────────────────────────────────────

def comparison_engine_node(state: AgentState) -> dict:
    """
    LangGraph node: compare retrieved properties against user requirements.

    Args:
        state: Current AgentState. Reads `parsed_query` and `retrieved_properties`.

    Returns:
        Partial state dict with `comparison_result` populated.
    """
    logger.info("comparison_engine: evaluating %d properties", len(state.retrieved_properties))

    llm = get_llm(streaming=False)

    user_message = _USER_PROMPT_TEMPLATE.format(
        parsed_query=json.dumps(state.parsed_query, ensure_ascii=False, indent=2),
        retrieved_properties=json.dumps(state.retrieved_properties, ensure_ascii=False, indent=2),
    )

    sys_prompt = _SYSTEM_PROMPT_INSIGHTS if state.data_intent == "insights_only" else _SYSTEM_PROMPT_RECOMMEND

    messages = [
        SystemMessage(content=sys_prompt),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    comparison_result = parse_llm_json(raw)
    if comparison_result is None:
        logger.error("comparison_engine: LLM returned non-JSON output:\n%s", raw)
        comparison_result = {"properties": [], "_parse_error": raw}

    logger.info(
        "comparison_engine: scored %d properties",
        len(comparison_result.get("properties", [])),
    )

    return {"comparison_result": comparison_result}
