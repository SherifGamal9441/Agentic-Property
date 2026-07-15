"""Deterministic evidence audit for scored listing candidates."""

from __future__ import annotations

import math
from typing import Any

from src.agents.state import AgentState


def _valid_score(item: dict[str, Any]) -> bool:
    evaluations = item.get("evaluations") or []
    weighted = [(evaluation, 3 if evaluation.get("priority") == "must_have" else 1) for evaluation in evaluations if evaluation.get("priority") != "deal_breaker" and evaluation.get("status") != "unsupported"]
    denominator = sum(weight for _, weight in weighted)
    expected = sum(weight for evaluation, weight in weighted if evaluation.get("status") == "matched") / denominator if denominator else 0.0
    return math.isclose(float(item.get("fit_score", -1)), expected, abs_tol=0.0001)


def reflection_node(state: AgentState) -> dict:
    """Withhold candidates whose identity, source, snapshot, or score cannot be audited."""
    raw_by_id = {
        str(item.get("property_id") or item.get("id") or index): item
        for index, item in enumerate(state.retrieved_properties)
    }
    valid: list[dict[str, Any]] = []
    issues: list[str] = []
    withheld_count = 0
    for scored in (state.comparison_result or {}).get("properties", []):
        property_id = str(scored.get("id", ""))
        raw = raw_by_id.get(property_id)
        property_issues = []
        if raw is None:
            property_issues.append("identity is absent from retrieved evidence")
        elif state.data_source != "active":
            property_issues.append("recommendations must come from the active snapshot")
        else:
            if not raw.get("link"):
                property_issues.append("listing source is missing")
            if not raw.get("post_date"):
                property_issues.append("snapshot observation date is missing")
        if not _valid_score(scored):
            property_issues.append("fit arithmetic is invalid")
        if property_issues:
            withheld_count += 1
            issues.extend(f"{property_id}: {issue}" for issue in property_issues)
        else:
            valid.append(scored)

    return {
        "comparison_result": {
            "properties": valid,
            "candidate_count": state.candidate_count or min(20, len(state.retrieved_properties)),
            "audited_count": state.audited_count or len((state.comparison_result or {}).get("properties", [])),
            "withheld_count": withheld_count,
        },
        "reflection_output": {"ok": not issues, "issues": issues, "withheld_count": withheld_count},
        "candidate_count": state.candidate_count or min(20, len(state.retrieved_properties)),
        "audited_count": state.audited_count or len((state.comparison_result or {}).get("properties", [])),
        "withheld_count": withheld_count,
    }


def route_after_reflection(_: AgentState) -> str:
    return "answer_generation"
