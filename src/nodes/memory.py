"""
Memory Node

Runs FIRST in the graph pipeline. Three responsibilities:
  1. Build conversation_context from conversation_history for downstream nodes.
  2. Classify every query as property_query, greeting, or meta_question.
  3. Short-circuit greetings and meta-questions directly to answer_generation,
     skipping the entire property pipeline.

Writes to state:
    conversation_context: str
    route: str | None        — set to "memory_greeting" or "memory_direct"
"""

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.state import AgentState
from src.llm.factory import get_llm

logger = logging.getLogger(__name__)

from src.prompts.loader import load_prompt

_PROMPTS = load_prompt("memory.yaml")
_SYSTEM_PROMPT = _PROMPTS["system_prompt"]
_USER_PROMPT_TEMPLATE = _PROMPTS["user_prompt_template"]

_MAX_HISTORY_TURNS = 10  # keep context manageable for small models


def _format_history_for_context(history: list[dict]) -> str:
    """Format conversation history as a readable string for prompt injection."""
    if not history:
        return "(No prior conversation — this is the first message.)"

    # Take last N messages to keep context window small
    recent = history[-(_MAX_HISTORY_TURNS * 2):]
    lines = []
    for msg in recent:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        # Truncate long messages
        if len(content) > 300:
            content = content[:297] + "..."
        lines.append(f"{role.upper()}: {content}")
    return "\n".join(lines)


def _parse_llm_response(raw: str) -> dict:
    """Parse LLM JSON response, with fallbacks for unparseable output."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    # Safe default: treat as property query (let it through the pipeline)
    logger.warning("memory: could not parse LLM response, defaulting to property_query")
    return {"category": "property_query"}


def memory_node(state: AgentState) -> dict:
    """
    LangGraph node: prepare conversation context, classify query, and route.

    Args:
        state: Current AgentState. Reads conversation_history and query.

    Returns:
        Partial state dict with conversation_context populated.
        Sets route="memory_greeting" or "memory_direct" for short-circuit paths.
    """
    logger.info("memory: building conversation context (%d prior turns)",
                len(state.conversation_history) // 2)

    # Build conversation context for downstream nodes
    context = _format_history_for_context(state.conversation_history)

    # Classify every query (greeting / meta / property)
    llm = get_llm(streaming=False)
    user_message = _USER_PROMPT_TEMPLATE.format(
        query=state.query,
        conversation_history=context,
    )
    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]
    response = llm.invoke(messages)
    raw = response.content.strip()
    result = _parse_llm_response(raw)

    category = result.get("category", "property_query")
    logger.info("memory: classified as %s (reason: %s)", category, result.get("reason", "?"))

    if category == "greeting":
        logger.info("memory: greeting detected — short-circuiting to answer_generation")
        return {
            "conversation_context": context,
            "route": "memory_greeting",
        }

    if category == "meta_question":
        logger.info("memory: meta-question detected — short-circuiting to answer_generation")
        return {
            "conversation_context": context,
            "route": "memory_direct",
        }

    return {"conversation_context": context}


def route_after_memory(state: AgentState) -> str:
    """
    Called by LangGraph's add_conditional_edges after memory_node runs.

    Returns:
        "query_relevancy" — normal property pipeline
        "answer_generation" — greeting or meta-question, skip the pipeline
    """
    if state.route in ("memory_greeting", "memory_direct"):
        return "answer_generation"
    return "query_relevancy"
