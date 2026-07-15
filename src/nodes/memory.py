"""Bounded checkpoint context restoration for the first graph node."""

import logging

from src.agents.state import AgentState

logger = logging.getLogger(__name__)

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
    """Restore bounded thread context without spending a model call."""
    logger.info("memory: building conversation context (%d prior turns)",
                len(state.conversation_history) // 2)
    context = _format_history_for_context(state.conversation_history)
    return {"conversation_context": context, "route": None}
