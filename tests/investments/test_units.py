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
