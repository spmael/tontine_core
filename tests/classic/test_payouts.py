from datetime import UTC, datetime
from decimal import Decimal

import pytest

from tontine.classic import ClassicPayout, ClassicPayoutRegistry
from tontine.exceptions import DuplicatePayoutError


def test_records_immutable_payout_with_historical_recipient() -> None:
    registry = ClassicPayoutRegistry()

    payout = registry.record(
        cycle_number=1,
        recipient_id="member-a",
        amount=Decimal("150000"),
        currency="JPY",
        recorded_at=datetime(2027, 1, 15, 12, 0, tzinfo=UTC),
        source_event="payout-001",
    )

    assert payout == ClassicPayout(
        cycle_number=1,
        recipient_id="member-a",
        amount=Decimal("150000"),
        currency="JPY",
        recorded_at=datetime(2027, 1, 15, 12, 0, tzinfo=UTC),
        source_event="payout-001",
    )
    with pytest.raises(AttributeError):
        payout.recipient_id = "member-b"  # type: ignore[misc]


def test_rejects_duplicate_payout_for_cycle() -> None:
    registry = ClassicPayoutRegistry()
    registry.record(
        cycle_number=1,
        recipient_id="member-a",
        amount=Decimal("150000"),
        currency="JPY",
        recorded_at=datetime(2027, 1, 15, 12, 0, tzinfo=UTC),
        source_event="payout-001",
    )

    with pytest.raises(DuplicatePayoutError):
        registry.record(
            cycle_number=1,
            recipient_id="member-b",
            amount=Decimal("150000"),
            currency="JPY",
            recorded_at=datetime(2027, 1, 15, 12, 0, tzinfo=UTC),
            source_event="payout-002",
        )


def test_rejects_invalid_payout_fields() -> None:
    invalid_payouts = (
        {"cycle_number": 0},
        {"recipient_id": " "},
        {"source_event": " "},
        {"recorded_at": datetime(2027, 1, 15, 12, 0)},
        {"amount": Decimal("-1")},
    )

    for invalid_fields in invalid_payouts:
        fields = {
            "cycle_number": 1,
            "recipient_id": "member-a",
            "amount": Decimal("150000"),
            "currency": "JPY",
            "recorded_at": datetime(2027, 1, 15, 12, 0, tzinfo=UTC),
            "source_event": "payout-001",
        }
        fields.update(invalid_fields)

        with pytest.raises(ValueError):
            ClassicPayout(**fields)
