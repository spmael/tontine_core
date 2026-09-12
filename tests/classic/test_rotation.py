from decimal import Decimal

import pytest

from tontine.classic import ClassicRotation


def test_five_member_jpy_rotation_selects_deterministic_recipients() -> None:
    rotation = ClassicRotation.from_active_members(
        active_member_ids=("member-a", "member-b", "member-c", "member-d", "member-e"),
    )

    assert rotation.recipient_for_cycle(1) == "member-a"
    assert rotation.recipient_for_cycle(5) == "member-e"
    assert rotation.recipient_for_cycle(6) == "member-a"
    assert rotation.expected_payout(
        {
            "member-a": Decimal("30000"),
            "member-b": Decimal("30000"),
            "member-c": Decimal("30000"),
            "member-d": Decimal("30000"),
            "member-e": Decimal("30000"),
        }
    ) == Decimal("150000")


def test_rotation_rejects_duplicate_or_missing_active_members() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        ClassicRotation.from_active_members(("member-a", "member-a"))

    with pytest.raises(ValueError, match="active members"):
        ClassicRotation.from_active_members(())


def test_rotation_rejects_unknown_contributors_and_negative_amounts() -> None:
    rotation = ClassicRotation.from_active_members(("member-a", "member-b"))

    with pytest.raises(ValueError, match="rotation"):
        rotation.expected_payout({"member-a": Decimal("30000")})

    with pytest.raises(ValueError, match="non-negative"):
        rotation.expected_payout(
            {"member-a": Decimal("30000"), "member-b": Decimal("-1")}
        )
