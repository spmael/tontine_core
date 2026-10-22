from decimal import Decimal

import pytest

from tontine.investments import (
    MemberUnitLedger,
    MemberUnitLedgerSnapshot,
    UnitIssueEvent,
    UnitRedemptionEvent,
)


def test_units_are_issued_and_redeemed_deterministically() -> None:
    ledger = MemberUnitLedger()

    ledger.issue("member-a", Decimal("30000"), Decimal("100"), "contribution-1")
    ledger.issue("member-b", Decimal("15000"), Decimal("100"), "contribution-2")
    ledger.redeem("member-a", Decimal("50"), "exit-1")

    assert ledger.balance_for("member-a") == Decimal("250")
    assert ledger.balance_for("member-b") == Decimal("150")
    assert ledger.total_units == Decimal("400")
    assert ledger.ownership_percentage_for("member-a") == Decimal("62.5")
    assert ledger.ownership_percentages() == {
        "member-a": Decimal("62.5"),
        "member-b": Decimal("37.5"),
    }


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


def test_issue_units_records_positive_quantity_under_unique_source_event() -> None:
    ledger = MemberUnitLedger()
    ledger.issue_units("member-a", Decimal("1.2500"), "allocation-1")

    assert ledger.balance_for("member-a") == Decimal("1.2500")
    with pytest.raises(ValueError, match="already"):
        ledger.issue_units("member-a", Decimal("1.2500"), "allocation-1")
    with pytest.raises(ValueError, match="greater than zero"):
        ledger.issue_units("member-a", Decimal("0"), "allocation-2")
    with pytest.raises(ValueError, match="identifier"):
        ledger.issue_units("", Decimal("1"), "allocation-3")


def test_snapshot_rebuilds_balances_from_ordered_unit_events() -> None:
    ledger = MemberUnitLedger()
    ledger.issue("member-a", Decimal("30000"), Decimal("100"), "issue-1")
    ledger.issue_units("member-b", Decimal("1.2500"), "issue-2")
    ledger.redeem("member-a", Decimal("50"), "redeem-1")

    snapshot = ledger.snapshot()
    restored = MemberUnitLedger.from_snapshot(snapshot)

    assert snapshot.schema_version == 1
    assert snapshot.events == (
        UnitIssueEvent("issue-1", "member-a", Decimal("300")),
        UnitIssueEvent("issue-2", "member-b", Decimal("1.2500")),
        UnitRedemptionEvent("redeem-1", "member-a", Decimal("50")),
    )
    assert restored.snapshot() == snapshot
    assert restored.balance_for("member-a") == Decimal("250")
    assert restored.balance_for("member-b") == Decimal("1.2500")
    assert restored.total_units == Decimal("251.2500")


def test_snapshot_rejects_unsupported_schema_duplicate_ids_and_invalid_order() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        MemberUnitLedgerSnapshot(events=(), schema_version=2)

    with pytest.raises(ValueError, match="already recorded"):
        MemberUnitLedgerSnapshot(
            events=(
                UnitIssueEvent("shared-event", "member-a", Decimal("1")),
                UnitRedemptionEvent("shared-event", "member-a", Decimal("0")),
            )
        )

    with pytest.raises(ValueError, match="exceeds"):
        MemberUnitLedgerSnapshot(
            events=(UnitRedemptionEvent("redeem-first", "member-a", Decimal("1")),)
        )


def test_failed_unit_operations_do_not_reserve_event_ids_or_change_balances() -> None:
    ledger = MemberUnitLedger()
    with pytest.raises(ValueError, match="greater than zero"):
        ledger.issue("member-a", Decimal("1"), Decimal("0"), "retryable-issue")
    with pytest.raises(ValueError, match="exceed"):
        ledger.redeem("member-a", Decimal("1"), "retryable-redemption")

    assert ledger.balance_for("member-a") == Decimal("0")
    assert ledger.snapshot().events == ()

    ledger.issue("member-a", Decimal("1"), Decimal("1"), "retryable-issue")
    ledger.redeem("member-a", Decimal("1"), "retryable-redemption")

    assert ledger.balance_for("member-a") == Decimal("0")


def test_unit_event_values_reject_empty_ids_and_negative_units() -> None:
    with pytest.raises(ValueError, match="identifier"):
        UnitIssueEvent("", "member-a", Decimal("1"))
    with pytest.raises(ValueError, match="identifier"):
        UnitRedemptionEvent("redeem-1", " ", Decimal("1"))
    with pytest.raises(ValueError, match="non-negative"):
        UnitIssueEvent("issue-1", "member-a", Decimal("-1"))
