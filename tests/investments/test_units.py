from decimal import Decimal

import pytest

from tontine.investments import MemberUnitLedger


def test_units_are_issued_and_redeemed_deterministically() -> None:
    ledger = MemberUnitLedger()

    ledger.issue("member-a", Decimal("30000"), Decimal("100"), "contribution-1")
    ledger.issue("member-b", Decimal("15000"), Decimal("100"), "contribution-2")
    ledger.redeem("member-a", Decimal("50"), "exit-1")

    assert ledger.balance_for("member-a") == Decimal("250")
    assert ledger.balance_for("member-b") == Decimal("150")
    assert ledger.total_units == Decimal("400")


def test_units_reject_duplicate_events_and_invalid_quantities() -> None:
    ledger = MemberUnitLedger()
    ledger.issue("member-a", Decimal("30000"), Decimal("100"), "contribution-1")

    with pytest.raises(ValueError, match="already"):
        ledger.issue("member-a", Decimal("30000"), Decimal("100"), "contribution-1")
    with pytest.raises(ValueError, match="non-negative"):
        ledger.redeem("member-a", Decimal("-1"), "exit-1")

    with pytest.raises(ValueError, match="identifier"):
        ledger.issue("member-a", Decimal("1"), Decimal("100"), "")
    with pytest.raises(ValueError, match="greater than zero"):
        ledger.issue("member-a", Decimal("1"), Decimal("0"), "contribution-2")
    with pytest.raises(ValueError, match="exceed"):
        ledger.redeem("member-a", Decimal("1000"), "exit-2")


def test_units_reject_invalid_values_and_unknown_members_start_empty() -> None:
    ledger = MemberUnitLedger()
    assert ledger.balance_for("missing") == Decimal("0")
    with pytest.raises(ValueError, match="non-negative"):
        ledger.issue("member-a", Decimal("-1"), Decimal("100"), "contribution-1")
    with pytest.raises(ValueError, match="valid decimal"):
        ledger.issue("member-a", "invalid", Decimal("100"), "contribution-2")
