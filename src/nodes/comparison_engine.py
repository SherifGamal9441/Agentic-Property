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
import re

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.state import AgentState
from src.llm.factory import get_llm

logger = logging.getLogger(__name__)

# ── Prompts ───────────────────────────────────────────────────────────────────

from src.prompts.loader import load_prompt

_PROMPTS = load_prompt("comparison_engine.yaml")
_SYSTEM_PROMPT_RECOMMEND = _PROMPTS["system_prompt_recommend"]
_SYSTEM_PROMPT_INSIGHTS = _PROMPTS["system_prompt_insights"]
_USER_PROMPT_TEMPLATE = _PROMPTS["user_prompt_template"]


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

    # ponytail: cap at 5 properties — 4B model truncates JSON with more
    properties = state.retrieved_properties[:5]
    if len(state.retrieved_properties) > 5:
        logger.info("comparison_engine: capping from %d to 5", len(state.retrieved_properties))

    llm = get_llm(streaming=False)

    user_message = _USER_PROMPT_TEMPLATE.format(
        parsed_query=json.dumps(state.parsed_query, ensure_ascii=False, indent=2),
        retrieved_properties=json.dumps(properties, ensure_ascii=False, indent=2),
    )

    sys_prompt = _SYSTEM_PROMPT_INSIGHTS if state.data_intent == "insights_only" else _SYSTEM_PROMPT_RECOMMEND

    messages = [
        SystemMessage(content=sys_prompt),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    try:
        comparison_result = json.loads(raw)
    except json.JSONDecodeError:
        # Attempt to extract JSON block if the model wrapped it despite instructions
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            comparison_result = json.loads(match.group())
        else:
            logger.error("comparison_engine: LLM returned non-JSON output:\n%s", raw)
            comparison_result = {"properties": [], "_parse_error": raw}

    logger.info(
        "comparison_engine: scored %d properties",
        len(comparison_result.get("properties", [])),
    )

    return {"comparison_result": comparison_result}
