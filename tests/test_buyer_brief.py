import pytest
from pydantic import ValidationError

from src.buyer_brief import BuyerBrief, Criterion


def test_buyer_brief_accepts_only_supported_verifiable_fields():
    brief = BuyerBrief(
        original_query="Ready 2BR in Dubai Marina under AED 2M",
        criteria=[
            Criterion(
                id="area",
                label="Dubai Marina",
                priority="must_have",
                field="area",
                operator="contains",
                value="Dubai Marina",
                verifiable=True,
            )
        ],
    )

    assert brief.version == 1
    assert brief.mode == "property_search"

    with pytest.raises(ValidationError):
        Criterion(
            id="view",
            label="Sea view",
            priority="nice_to_have",
            field="view",
            operator="contains",
            value="sea",
            verifiable=True,
        )


def test_lifestyle_criterion_must_be_explicitly_unverifiable():
    criterion = Criterion(
        id="quiet",
        label="Quiet surroundings",
        priority="nice_to_have",
        field=None,
        operator=None,
        value=None,
        verifiable=False,
    )

    assert criterion.verifiable is False


def test_verifiable_criterion_requires_field_operator_and_value():
    with pytest.raises(ValidationError):
        Criterion(
            id="budget",
            label="Under AED 2M",
            priority="must_have",
            field="price",
            operator=None,
            value=2_000_000,
            verifiable=True,
        )
