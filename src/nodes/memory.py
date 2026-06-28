"""
Memory Node

Runs FIRST in the graph pipeline. Two responsibilities:
  1. Build conversation_context from conversation_history for downstream nodes.
  2. Detect meta-questions (queries about the conversation itself) and
     short-circuit the pipeline — skipping the property nodes entirely
     and passing only conversation history to answer_generation.

Writes to state:
    conversation_context: str
    route: str | None        — set to "memory_direct" for meta-questions
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


def memory_node(state: AgentState) -> dict:
    """
    LangGraph node: prepare conversation context and detect meta-questions.

    Args:
        state: Current AgentState. Reads conversation_history and query.

    Returns:
        Partial state dict with conversation_context populated.
        If meta-question detected, also sets route="memory_direct".
    """
    logger.info("memory: building conversation context (%d prior turns)",
                len(state.conversation_history) // 2)

    # Build conversation context for downstream nodes
    context = _format_history_for_context(state.conversation_history)

    # Only run meta-detection LLM call when there's prior history
    if state.conversation_history:
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

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                logger.warning("memory: could not parse meta-detection response, assuming non-meta")
                result = {"is_meta": False}

        is_meta = result.get("is_meta", False)
        if is_meta:
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
        "query_relevancy" — normal pipeline
        "answer_generation" — meta-question, skip the pipeline
    """
    if state.route == "memory_direct":
        return "answer_generation"
    return "query_relevancy"
