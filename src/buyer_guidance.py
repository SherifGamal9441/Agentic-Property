"""Validated property-guidance references for audited buyer results."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.buyer_brief import BuyerBrief


ReasonCode = Literal[
    "all_verifiable_criteria_matched",
    "highest_fit",
    "highest_evidence",
    "lowest_price_tiebreak",
]
CaveatStatus = Literal["conflict", "unknown", "unsupported"]


class GuidanceReason(BaseModel):
    model_config = ConfigDict(extra="forbid")

    property_id: str = Field(min_length=1)
    code: ReasonCode
    criterion_ids: list[str] = Field(default_factory=list)


class GuidanceCaveat(BaseModel):
    model_config = ConfigDict(extra="forbid")

    property_id: str | None = None
    criterion_id: str
    status: CaveatStatus


class PropertyGuidance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[1] = 1
    outcome: Literal["matches", "conditional", "no_match"]
    best_match_id: str | None = None
    runner_up_id: str | None = None
    reasons: list[GuidanceReason] = Field(default_factory=list)
    caveats: list[GuidanceCaveat] = Field(default_factory=list)
    next_action: Literal["review_best_match", "compare_matches", "edit_brief"]


def validate_guidance(
    guidance: PropertyGuidance,
    brief: BuyerBrief,
    properties: list[dict],
) -> PropertyGuidance:
    """Reject references or outcomes that disagree with audited ordering."""
    eligible = [item for item in properties if item.get("suitability") != "excluded"]
    suitable = [item for item in eligible if item.get("suitability") == "suitable"]
    expected_outcome = "matches" if suitable else ("conditional" if eligible else "no_match")
    expected_best = str(eligible[0]["id"]) if eligible else None
    expected_runner = str(eligible[1]["id"]) if len(eligible) > 1 else None
    if (guidance.outcome, guidance.best_match_id, guidance.runner_up_id) != (
        expected_outcome,
        expected_best,
        expected_runner,
    ):
        raise ValueError("Guidance outcome or ranking disagrees with audited results.")

    properties_by_id = {str(item["id"]): item for item in eligible}
    criteria_by_id = {item.id: item for item in brief.criteria}
    for reason in guidance.reasons:
        if reason.property_id not in properties_by_id:
            raise ValueError("Guidance reason references an unknown property.")
        if any(criterion_id not in criteria_by_id for criterion_id in reason.criterion_ids):
            raise ValueError("Guidance reason references an unknown criterion.")
        statuses = {
            item.get("criterion_id"): item.get("status")
            for item in properties_by_id[reason.property_id].get("evaluations", [])
        }
        if any(statuses.get(criterion_id) != "matched" for criterion_id in reason.criterion_ids):
            raise ValueError("Guidance reason promotes evidence that was not matched.")
    for caveat in guidance.caveats:
        if caveat.criterion_id not in criteria_by_id:
            raise ValueError("Guidance caveat references an unknown criterion.")
        if caveat.property_id is None:
            if caveat.status != "unsupported" or criteria_by_id[caveat.criterion_id].verifiable:
                raise ValueError("Global caveats must reference unsupported criteria.")
            continue
        property_data = properties_by_id.get(caveat.property_id)
        if property_data is None:
            raise ValueError("Guidance caveat references an unknown property.")
        statuses = {
            item.get("criterion_id"): item.get("status")
            for item in property_data.get("evaluations", [])
        }
        if statuses.get(caveat.criterion_id) != caveat.status:
            raise ValueError("Guidance caveat disagrees with audited evidence.")
    return guidance
