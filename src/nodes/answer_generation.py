"""
Answer Generation Node

Takes the comparison engine's result and the reflection audit, then produces
a final, user-facing recommendation — streamed token by token.

Reads from state:
    query               — original user question
    comparison_result   — scored properties from comparison_engine_node
    reflection_output   — audit notes from reflection_node

Writes to state:
    final_answer: str   — the complete streamed response
"""

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.state import AgentState
from src.llm.factory import get_llm

logger = logging.getLogger(__name__)

# ── Prompt templates ──────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a knowledgeable and trustworthy UAE real estate advisor.
Your job is to take a property comparison report and give the user a clear,
honest recommendation they can act on.

Guidelines:
- Lead with the best match and explain WHY using specific data (fit_score, criteria, price assessment).
- If there is a close runner-up, mention it briefly with its key differentiator.
- If the reflection audit flagged any issues or caveats, include them transparently at the end.
- Be concise. No filler phrases ("Great question!", "Certainly!", etc.).
- Write in plain English — avoid technical JSON terms like "fit_score" in the final output.
"""

_USER_PROMPT_TEMPLATE = """\
User's original request:
{query}

Property comparison report:
{comparison_result}

Quality review notes (use these as caveats if relevant):
{reflection_issues}

Write the final recommendation for the user.
Structure:
1. Best match — name it and give 2–3 specific reasons why it fits best.
2. Runner-up (if any) — name it and its one key advantage over the best match.
3. Caveats — any important limitations or data gaps the user should know about.
"""


# ── Node function ─────────────────────────────────────────────────────────────

def answer_generation_node(state: AgentState) -> dict:
    """
    LangGraph node: generate the final user-facing answer with streaming.

    Args:
        state: Current AgentState. Reads `query`, `comparison_result`,
               and `reflection_output`.

    Returns:
        Partial state dict with `final_answer` populated.
    """
    logger.info("answer_generation: building final recommendation")

    llm = get_llm(streaming=True)

    reflection_issues = (
        state["reflection_output"].get("issues", [])
        if state.get("reflection_output")
        else []
    )

    user_message = _USER_PROMPT_TEMPLATE.format(
        query=state["query"],
        comparison_result=_format_comparison_for_prompt(state["comparison_result"]),
        reflection_issues="\n".join(f"- {issue}" for issue in reflection_issues) or "None",
    )

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    # Stream tokens — collect into full string for state storage
    final_answer_chunks: list[str] = []
    for chunk in llm.stream(messages):
        token = chunk.content
        final_answer_chunks.append(token)
        print(token, end="", flush=True)   # live streaming to stdout / API layer

    print()  # newline after stream ends
    final_answer = "".join(final_answer_chunks)

    logger.info("answer_generation: response complete (%d chars)", len(final_answer))

    return {"final_answer": final_answer}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_comparison_for_prompt(comparison_result: dict | None) -> str:
    """
    Convert the structured comparison_result into a readable text block
    so the LLM doesn't have to parse raw JSON in its prompt.
    """
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
