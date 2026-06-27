"""
Answer Generation Node

Single node for ALL graph paths. Inspects state and generates the right
user-facing response depending on what data is available:

  Path A — query_routing → comparison_engine → reflection → HERE
      Reads: comparison_result, reflection_output, data_intent
      data_intent="recommend"     → recommends best match with reasons
      data_intent="insights_only" → derives market insights only;
                                    explicitly states properties may be unavailable

  Path B — query_understanding → web_search → HERE
      Reads: web_search_summary
      Answers the general question concisely

  Path C — query_relevancy (out-of-scope) → END (never reaches here)
      final_answer is already set by query_relevancy_node directly

The API layer always reads state.final_answer — one field, all paths.

Writes to state:
    final_answer: str
"""

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.state import AgentState
from src.llm.factory import get_llm

logger = logging.getLogger(__name__)

# ── Prompts (shared across all paths) ───────────────────────────────────────────

from src.prompts.loader import load_prompt

_PROMPTS = load_prompt("answer_generation.yaml")
_SYSTEM_PROMPT = _PROMPTS["system_prompt"]
_RECOMMEND_TEMPLATE = _PROMPTS["recommend_template"]
_INSIGHTS_TEMPLATE = _PROMPTS["insights_template"]
_WEB_SEARCH_TEMPLATE = _PROMPTS["web_search_template"]
_NO_RESULTS_TEMPLATE = _PROMPTS["no_results_template"]


# ── Node function ─────────────────────────────────────────────────────────────

def answer_generation_node(state: AgentState) -> dict:
    """
    LangGraph node: generate the final user-facing response.

    Detects which path ran by inspecting state, then builds the appropriate
    prompt and streams the LLM response.

    Args:
        state: Current AgentState.

    Returns:
        Partial state dict with `final_answer` populated.
    """
    llm = get_llm(streaming=True)
    messages = _build_messages(state)

    logger.info("answer_generation: streaming response")

    chunks: list[str] = []
    for chunk in llm.stream(messages):
        token = chunk.content
        chunks.append(token)
        print(token, end="", flush=True)

    print()
    final_answer = "".join(chunks)

    logger.info("answer_generation: response complete (%d chars)", len(final_answer))
    return {"final_answer": final_answer}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_messages(state: AgentState) -> list:
    """Choose the right prompt template based on what data is in state."""

    # ── web_search path ───────────────────────────────────────────────────────
    if state.web_search_summary:
        logger.info("answer_generation: web_search path")
        user_content = _WEB_SEARCH_TEMPLATE.format(
            query=state.query,
            web_search_summary=state.web_search_summary,
        )
        return [SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=user_content)]

    # ── query_routing path ────────────────────────────────────────────────────
    reflection_issues = (
        state.reflection_output.get("issues", []) if state.reflection_output else []
    )
    reflection_text = "\n".join(f"- {i}" for i in reflection_issues) or "None"
    comparison_text = _format_comparison_for_prompt(state.comparison_result)
    currency_note = _build_currency_note(state)

    # No properties found at all
    if not state.retrieved_properties and not state.comparison_result:
        logger.info("answer_generation: no-results path")
        user_content = _NO_RESULTS_TEMPLATE.format(query=state.query)
        return [SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=user_content)]

    # Historical data — insights only
    if state.data_intent == "insights_only":
        logger.info("answer_generation: insights_only path (historical data)")
        user_content = _INSIGHTS_TEMPLATE.format(
            query=state.query,
            comparison_result=comparison_text,
            reflection_issues=reflection_text,
        )
        if currency_note:
            user_content += f"\n\n{currency_note}"
        return [SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=user_content)]

    # Recommend — current cached data
    logger.info("answer_generation: recommend path (cached data)")
    user_content = _RECOMMEND_TEMPLATE.format(
        query=state.query,
        comparison_result=comparison_text,
        reflection_issues=reflection_text,
    )
    if currency_note:
        user_content += f"\n\n{currency_note}"
    return [SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=user_content)]


def _build_currency_note(state: AgentState) -> str:
    """Build a note for the LLM to show dual-currency prices when applicable."""
    if not state.exchange_rate or state.currency == "AED":
        return ""
    return (
        f"Currency note: The user expressed their budget in {state.currency}. "
        f"Exchange rate used: 1 {state.currency} = {state.exchange_rate:.2f} AED. "
        f"When mentioning prices, show them in AED followed by the equivalent "
        f"in {state.currency} (divide AED by {state.exchange_rate:.2f})."
    )


def _format_comparison_for_prompt(comparison_result: dict | None) -> str:
    """Convert comparison_result JSON into a readable text block for the prompt."""
    if not comparison_result:
        return "No comparison data available."

    properties = comparison_result.get("properties", [])
    if not properties:
        return "No properties were compared."

    lines: list[str] = []
    for prop in sorted(properties, key=lambda p: p.get("fit_score", 0), reverse=True):
        lines.append(f"Property: {prop.get('title', 'Unknown')} (ID: {prop.get('id', '?')})")
        lines.append(f"  Fit score    : {prop.get('fit_score', 'N/A')}")
        lines.append(f"  Price        : {prop.get('price_assessment', 'N/A')}")
        lines.append(f"  Matches      : {', '.join(prop.get('matched_criteria', [])) or 'none'}")
        lines.append(f"  Gaps         : {', '.join(prop.get('unmatched_criteria', [])) or 'none'}")
        lines.append("")

    return "\n".join(lines)
