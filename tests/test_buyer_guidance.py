import pytest

from src.buyer_brief import BuyerBrief, Criterion
from src.buyer_guidance import PropertyGuidance, validate_guidance


def _brief() -> BuyerBrief:
    return BuyerBrief(
        original_query="Furnished home in Business Bay",
        criteria=[
            Criterion(id="area", label="Business Bay", priority="must_have", field="area", operator="contains", value="Business Bay"),
            Criterion(id="view", label="Water view", priority="nice_to_have", field=None, operator=None, value=None, verifiable=False),
        ],
    )


def _properties() -> list[dict]:
    return [
        {
            "id": "best",
            "suitability": "suitable",
            "evaluations": [
                {"criterion_id": "area", "status": "matched"},
                {"criterion_id": "view", "status": "unsupported"},
            ],
        },
        {"id": "runner", "suitability": "suitable", "evaluations": []},
    ]


def test_guidance_accepts_audited_order_and_caveats():
    guidance = PropertyGuidance(
        outcome="matches",
        best_match_id="best",
        runner_up_id="runner",
        reasons=[{"property_id": "best", "code": "highest_fit", "criterion_ids": ["area"]}],
        caveats=[{"property_id": "best", "criterion_id": "view", "status": "unsupported"}],
        next_action="review_best_match",
    )

    assert validate_guidance(guidance, _brief(), _properties()) is guidance


def test_guidance_rejects_model_reranking():
    guidance = PropertyGuidance(
        outcome="matches",
        best_match_id="runner",
        runner_up_id="best",
        next_action="compare_matches",
    )

    with pytest.raises(ValueError, match="ranking"):
        validate_guidance(guidance, _brief(), _properties())


def test_guidance_rejects_caveat_that_disagrees_with_evidence():
    guidance = PropertyGuidance(
        outcome="matches",
        best_match_id="best",
        runner_up_id="runner",
        caveats=[{"property_id": "best", "criterion_id": "area", "status": "unknown"}],
        next_action="review_best_match",
    )

    with pytest.raises(ValueError, match="disagrees"):
        validate_guidance(guidance, _brief(), _properties())


def test_guidance_rejects_unknown_or_unsupported_positive_reason():
    guidance = PropertyGuidance(
        outcome="matches",
        best_match_id="best",
        runner_up_id="runner",
        reasons=[{"property_id": "best", "code": "highest_evidence", "criterion_ids": ["view"]}],
        next_action="review_best_match",
    )

    with pytest.raises(ValueError, match="not matched"):
        validate_guidance(guidance, _brief(), _properties())
