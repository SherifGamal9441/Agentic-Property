"""
Reflection Node

Audits the output of the Comparison Engine — NOT the retrieved data, NOT user intent.
It asks: "Is this comparison result accurate, complete, and internally consistent?"

Reads from state:
    comparison_result   — the dict produced by comparison_engine_node

Writes to state:
    reflection_output: {
        ok: bool,               # True if comparison passes quality check
        issues: list[str],      # Detected problems (empty when ok=True)
        confidence: float,      # 0.0–1.0 overall confidence in the comparison
    }
    needs_retry: bool           # True when ok=False and retries remain
    retry_tool: str | None      # Suggested tool to retry with (set by upstream router)
    retry_count: int            # Incremented on each retry
"""

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.state import AgentState
from config.pydantic.settings import settings
from src.llm.factory import get_llm

logger = logging.getLogger(__name__)

# ── Prompt templates ──────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a quality-control agent reviewing a real estate property comparison report.
Your sole job is to audit the comparison report itself — not the original user query,
not the underlying property data.

Check for these problems:
1. Missing or null required fields (id, title, fit_score, matched_criteria, unmatched_criteria, price_assessment)
2. Inconsistent fit_score — e.g. all criteria matched but score < 0.5, or major gaps but score > 0.8
3. Empty matched_criteria AND empty unmatched_criteria (the LLM did not do its job)
4. Invalid price_assessment value (must be "below_market", "fair", or "above_market")
5. Zero properties in the comparison (nothing was compared)

Return ONLY valid JSON — no prose, no markdown fences.
"""

_USER_PROMPT_TEMPLATE = """\
Comparison report to audit:
{comparison_result}

Return a JSON object with exactly these fields:
{{
  "ok": true | false,
  "issues": ["<description of issue>", ...],   // empty array when ok=true
  "confidence": <float 0.0 to 1.0>
}}
"""


# ── Node function ─────────────────────────────────────────────────────────────

def reflection_node(state: AgentState) -> dict:
    """
    LangGraph node: audit the comparison engine's output for quality.

    Args:
        state: Current AgentState. Reads `comparison_result` and `retry_count`.

    Returns:
        Partial state dict updating `reflection_output`, `needs_retry`,
        `retry_tool`, and `retry_count`.
    """
    logger.info("reflection: auditing comparison result")

    llm = get_llm(streaming=False)

    user_message = _USER_PROMPT_TEMPLATE.format(
        comparison_result=json.dumps(state.comparison_result, ensure_ascii=False, indent=2),
    )

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    try:
        reflection_output = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            reflection_output = json.loads(match.group())
        else:
            logger.error("reflection: LLM returned non-JSON output:\n%s", raw)
            # Fail safe: treat as failed quality check so we can retry or escalate
            reflection_output = {
                "ok": False,
                "issues": ["reflection node could not parse LLM response"],
                "confidence": 0.0,
            }

    ok: bool = reflection_output.get("ok", False)
    current_retry_count: int = state.retry_count
    needs_retry = not ok and current_retry_count < settings.max_retries

    if needs_retry:
        logger.warning(
            "reflection: comparison failed quality check (retry %d/%d). Issues: %s",
            current_retry_count + 1,
            settings.max_retries,
            reflection_output.get("issues", []),
        )
    else:
        logger.info(
            "reflection: comparison passed (ok=%s, confidence=%.2f)",
            ok,
            reflection_output.get("confidence", 0.0),
        )

    return {
        "reflection_output": reflection_output,
        "needs_retry": needs_retry,
        "retry_count": current_retry_count + (1 if needs_retry else 0),
    }


# ── Conditional edge router ───────────────────────────────────────────────────

def route_after_reflection(state: AgentState) -> str:
    """
    Called by LangGraph's add_conditional_edges after the reflection node runs.

    Returns:
        "answer_generation" — comparison passed, proceed to final answer
        "tool_router"       — comparison failed, signal upstream to retry
    """
    if state.needs_retry:
        return "tool_router"
    return "answer_generation"
