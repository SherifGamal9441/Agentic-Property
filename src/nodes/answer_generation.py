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

  Path D — memory (greeting) → HERE
      Reads: state.query
      Generates a warm, natural greeting response with examples

  Path E — memory (meta_question) → HERE
      Reads: conversation_context
      Answers questions about the conversation itself

The API layer always reads state.final_answer — one field, all paths.

Writes to state:
    final_answer: str
"""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from src.agents.state import AgentState
from src.buyer_guidance import PropertyGuidance, validate_guidance
from src.llm.factory import get_llm
from src.utils import parse_llm_json

logger = logging.getLogger(__name__)

# ── Prompts (shared across all paths) ───────────────────────────────────────────

from pathlib import Path as _Path
import yaml as _yaml

_PROMPTS_DIR = _Path(__file__).parent.parent / "prompts"

_PROMPTS = _yaml.safe_load((_PROMPTS_DIR / "answer_generation.yaml").read_text(encoding="utf-8"))
_SYSTEM_PROMPT = _PROMPTS["system_prompt"]
_RECOMMEND_TEMPLATE = _PROMPTS["recommend_template"]
_INSIGHTS_TEMPLATE = _PROMPTS["insights_template"]
_WEB_SEARCH_TEMPLATE = _PROMPTS["web_search_template"]
_NO_RESULTS_TEMPLATE = _PROMPTS["no_results_template"]
_GREETING_TEMPLATE = _PROMPTS["greeting_template"]


# ── Node function ─────────────────────────────────────────────────────────────

def answer_generation_node(state: AgentState) -> dict:
    """
    LangGraph node: generate the final user-facing response.

    Detects which path ran by inspecting state, then builds the appropriate
    prompt and streams the LLM response. Also appends the current turn
    (user query + assistant answer) to conversation_history.

    Args:
        state: Current AgentState.

    Returns:
        Partial state dict with `final_answer` and `conversation_history` populated.
    """
    if (
        state.buyer_brief
        and state.buyer_brief.mode == "property_search"
        and state.route not in {"memory_direct", "memory_greeting", "web_search"}
        and state.data_intent != "insights_only"
    ):
        return _structured_property_answer(state)

    llm = get_llm(streaming=True)
    messages = _build_messages(state)

    logger.info("answer_generation: streaming response")

    chunks: list[str] = []
    for chunk in llm.stream(messages):
        token = chunk.content
        chunks.append(token)
    final_answer = "".join(chunks)

    # Append this turn to conversation history
    new_entries = [
        {"role": "user", "content": state.query},
        {"role": "assistant", "content": final_answer},
    ]
    updated_history = state.conversation_history + new_entries

    logger.info("answer_generation: response complete (%d chars, %d total turns)",
                len(final_answer), len(updated_history) // 2)
    return {
        "final_answer": final_answer,
        "conversation_history": updated_history,
    }


def _structured_property_answer(state: AgentState) -> dict:
    """Ask the live model for references only, then validate every reference."""
    properties = (state.comparison_result or {}).get("properties", [])
    schema = json.dumps(PropertyGuidance.model_json_schema(), ensure_ascii=False)
    evidence = json.dumps(
        {
            "brief": state.buyer_brief.model_dump(),
            "audited_properties": [
                {
                    "id": item.get("id"),
                    "suitability": item.get("suitability"),
                    "fit_score": item.get("fit_score"),
                    "evidence_coverage": item.get("evidence_coverage"),
                    "evaluations": item.get("evaluations", []),
                }
                for item in properties
                if item.get("suitability") != "excluded"
            ],
        },
        ensure_ascii=False,
    )
    system = SystemMessage(content=(
        "Return one PropertyGuidance JSON object only. Use only supplied property and criterion IDs. "
        "The first audited property is best and the second is runner-up. Do not write prose, facts, "
        "scores, prices, or reasoning outside the schema. Schema: " + schema
    ))
    llm = get_llm(streaming=False)
    raw = str(llm.invoke([system, HumanMessage(content=evidence)]).content).strip()
    guidance: PropertyGuidance | None = None
    for attempt in range(2):
        try:
            guidance = validate_guidance(
                PropertyGuidance.model_validate(parse_llm_json(raw)),
                state.buyer_brief,
                properties,
            )
            break
        except (ValidationError, json.JSONDecodeError, TypeError, ValueError):
            if attempt == 1:
                raise ValueError("The selected model could not produce valid property guidance.")
            repair = llm.invoke([
                system,
                HumanMessage(content=(
                    "Correct the previous response using the evidence below. Return JSON only.\n\n" + evidence
                )),
            ])
            raw = str(repair.content).strip()

    final_answer = _guidance_history_text(guidance, properties, state)
    updated_history = state.conversation_history + [
        {"role": "user", "content": state.query},
        {"role": "assistant", "content": final_answer},
    ]
    return {
        "buyer_guidance": guidance,
        "final_answer": final_answer,
        "conversation_history": updated_history,
    }


def _guidance_history_text(
    guidance: PropertyGuidance,
    properties: list[dict],
    state: AgentState,
) -> str:
    """Keep conversation memory readable without trusting generated property prose."""
    by_id = {str(item.get("id")): item for item in properties}
    if guidance.outcome == "no_match":
        return "No exact data-snapshot match met the structured brief; no criterion was relaxed."
    best = by_id.get(str(guidance.best_match_id), {})
    parts = [f"Best match: {best.get('title', guidance.best_match_id)}."]
    if guidance.runner_up_id:
        runner = by_id.get(str(guidance.runner_up_id), {})
        parts.append(f"Runner-up: {runner.get('title', guidance.runner_up_id)}.")
    criterion_labels = {item.id: item.label for item in state.buyer_brief.criteria}
    caveats = [criterion_labels.get(item.criterion_id, item.criterion_id) for item in guidance.caveats]
    parts.append(
        "Evidence gaps: " + ", ".join(dict.fromkeys(caveats)) + "."
        if caveats
        else "No known criterion gaps in the captured fields."
    )
    return " ".join(parts)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_messages(state: AgentState) -> list:
    """Choose the right prompt template based on what data is in state."""

    # Build system prompt with conversation context when available
    system_with_context = _SYSTEM_PROMPT
    if state.conversation_context and "(No prior conversation" not in state.conversation_context:
        system_with_context += (
            f"\n\nPrior conversation for context:\n{state.conversation_context}"
        )

    # ── Meta-question / memory direct path ──────────────────────────────────
    if state.route == "memory_direct":
        logger.info("answer_generation: memory direct path (meta-question)")
        user_content = (
            f"User query: {state.query}\n\n"
            f"Here is the conversation history. Answer based on what you find in it. "
            f"If you cannot answer from the history, say so honestly.\n\n"
            f"{state.conversation_context}"
        )
        return [SystemMessage(content=system_with_context), HumanMessage(content=user_content)]

    # ── Greeting / small-talk path ──────────────────────────────────────────
    if state.route == "memory_greeting":
        logger.info("answer_generation: greeting path")
        user_content = _GREETING_TEMPLATE.format(query=state.query)
        return [SystemMessage(content=system_with_context), HumanMessage(content=user_content)]

    # ── web_search path ───────────────────────────────────────────────────────
    if state.web_search_summary:
        logger.info("answer_generation: web_search path")
        user_content = _WEB_SEARCH_TEMPLATE.format(
            query=state.query,
            web_search_summary=state.web_search_summary,
        )
        return [SystemMessage(content=system_with_context), HumanMessage(content=user_content)]

    # ── query_routing path ────────────────────────────────────────────────────
    reflection_issues = (
        state.reflection_output.get("issues", []) if state.reflection_output else []
    )
    reflection_text = "\n".join(f"- {i}" for i in reflection_issues) or "None"
    compared_properties = (
        state.comparison_result.get("properties", []) if state.comparison_result else []
    )
    eligible_properties = [
        prop for prop in compared_properties if prop.get("suitability") != "excluded"
    ]
    comparison_text = _format_comparison_for_prompt(state.comparison_result)
    currency_note = _build_currency_note(state)

    # No eligible properties found. Excluded rows never enter buyer guidance.
    if not eligible_properties and state.data_intent != "insights_only":
        logger.info("answer_generation: no-results path")
        user_content = _NO_RESULTS_TEMPLATE.format(query=state.query)
        return [SystemMessage(content=system_with_context), HumanMessage(content=user_content)]

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
        return [SystemMessage(content=system_with_context), HumanMessage(content=user_content)]

    # Recommend — listing data snapshot
    logger.info("answer_generation: recommend path (listing snapshot)")
    user_content = _RECOMMEND_TEMPLATE.format(
        query=state.query,
        comparison_result=comparison_text,
        reflection_issues=reflection_text,
    )
    if currency_note:
        user_content += f"\n\n{currency_note}"
    return [SystemMessage(content=system_with_context), HumanMessage(content=user_content)]


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

    compared_properties = comparison_result.get("properties", [])
    if not compared_properties:
        return "No properties were compared."

    properties = [
        prop
        for prop in compared_properties
        if prop.get("suitability") != "excluded"
    ]
    if not properties:
        return "No eligible properties were compared."

    lines: list[str] = []
    for prop in sorted(properties, key=lambda p: p.get("fit_score", 0), reverse=True):
        lines.append(f"Property: {prop.get('title', 'Unknown')} (ID: {prop.get('id', '?')})")
        lines.append(f"  Fit score    : {prop.get('fit_score', 'N/A')}")
        lines.append(f"  Suitability  : {prop.get('suitability', 'conditional')}")
        lines.append(f"  Evidence     : {prop.get('evidence_coverage', 'N/A')}")
        lines.append(f"  Matches      : {', '.join(prop.get('matched_criteria', [])) or 'none'}")
        lines.append(f"  Gaps         : {', '.join(prop.get('unmatched_criteria', [])) or 'none'}")
        lines.append(f"  Unsupported  : {', '.join(prop.get('unsupported_criteria', [])) or 'none'}")
        lines.append("")

    return "\n".join(lines)
