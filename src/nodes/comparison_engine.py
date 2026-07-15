"""Deterministic criterion evaluation for frozen active-listing evidence."""

from __future__ import annotations

import logging
from typing import Any

from src.agents.state import AgentState
from src.buyer_brief import BuyerBrief, Criterion, property_value
from src.llm.factory import get_llm  # compatibility seam; deterministic scoring never calls it

logger = logging.getLogger(__name__)


def _normalise(value: Any) -> Any:
    return value.casefold().strip() if isinstance(value, str) else value


def _normalise_completion_status(value: Any) -> Any:
    normalised = _normalise(value)
    if not isinstance(normalised, str):
        return normalised
    compact = normalised.replace("_", "-").replace(" ", "-")
    if compact in {"ready", "completed", "complete"}:
        return "completed"
    if compact in {"off-plan", "offplan", "under-construction"}:
        return "under-construction"
    return compact


def _matches(actual: Any, criterion: Criterion) -> bool:
    expected = criterion.value
    if criterion.operator == "contains":
        return str(expected).casefold() in str(actual).casefold()
    if criterion.field == "completion_status":
        left = _normalise_completion_status(actual)
        right = _normalise_completion_status(expected)
    else:
        left, right = _normalise(actual), _normalise(expected)
    if criterion.operator == "eq":
        return left == right
    if criterion.operator == "not_eq":
        return left != right
    try:
        if criterion.operator == "gte":
            return left >= right
        if criterion.operator == "lte":
            return left <= right
    except TypeError:
        return False
    return False


def _evaluate(property_data: dict[str, Any], criterion: Criterion) -> dict[str, Any]:
    if not criterion.verifiable or criterion.field is None:
        status = "unsupported"
        actual = None
    else:
        actual = property_value(property_data, criterion.field)
        status = "unknown" if actual is None else ("matched" if _matches(actual, criterion) else "conflict")
    return {
        "criterion_id": criterion.id,
        "label": criterion.label,
        "priority": criterion.priority,
        "status": status,
        "actual": actual,
    }


def _score(property_data: dict[str, Any], brief: BuyerBrief, index: int) -> dict[str, Any]:
    evaluations = [_evaluate(property_data, criterion) for criterion in brief.criteria]
    hard = [item for item in evaluations if item["priority"] in {"must_have", "deal_breaker"}]
    if any(item["status"] == "conflict" for item in hard):
        suitability = "excluded"
    elif any(item["status"] == "unknown" for item in hard):
        suitability = "conditional"
    else:
        suitability = "suitable"

    weighted = [(item, 3 if item["priority"] == "must_have" else 1) for item in evaluations if item["priority"] != "deal_breaker" and item["status"] != "unsupported"]
    denominator = sum(weight for _, weight in weighted)
    numerator = sum(weight for item, weight in weighted if item["status"] == "matched")
    fit_score = numerator / denominator if denominator else 0.0
    verified = sum(item["status"] in {"matched", "conflict"} for item in evaluations)
    coverage = verified / len(evaluations) if evaluations else 1.0

    property_id = str(property_data.get("property_id") or property_data.get("id") or index)
    area = property_data.get("area_name") or property_data.get("area") or "Dubai"
    title = property_data.get("title") or property_data.get("building_name") or property_data.get("address") or f"{area} residence"
    matched = [item["label"] for item in evaluations if item["status"] == "matched"]
    conflicts = [item["label"] for item in evaluations if item["status"] == "conflict"]
    unknown = [item["label"] for item in evaluations if item["status"] == "unknown"]
    unsupported = [item["label"] for item in evaluations if item["status"] == "unsupported"]
    return {
        "id": property_id,
        "title": title,
        "fit_score": fit_score,
        "evidence_coverage": coverage,
        "suitability": suitability,
        "evaluations": evaluations,
        "matched_criteria": matched,
        "conflicting_criteria": conflicts,
        "unknown_criteria": unknown,
        "unsupported_criteria": unsupported,
        "unmatched_criteria": conflicts + unknown,
    }


def comparison_engine_node(state: AgentState) -> dict:
    """Score up to 20 active candidates without asking an LLM to calculate fit."""
    brief = state.buyer_brief or BuyerBrief(original_query=state.query or "Legacy query", criteria=[])
    results = [_score(item, brief, index) for index, item in enumerate(state.retrieved_properties[:20])]
    suitability_rank = {"suitable": 0, "conditional": 1, "excluded": 2}
    raw_by_id = {str(item.get("property_id") or item.get("id") or index): item for index, item in enumerate(state.retrieved_properties)}
    results.sort(
        key=lambda item: (
            suitability_rank[item["suitability"]],
            -item["fit_score"],
            -item["evidence_coverage"],
            raw_by_id.get(item["id"], {}).get("price") if isinstance(raw_by_id.get(item["id"], {}).get("price"), (int, float)) else float("inf"),
            item["id"],
        )
    )
    logger.info("comparison_engine: deterministically evaluated %d properties", len(results))
    return {"comparison_result": {"properties": results}}
