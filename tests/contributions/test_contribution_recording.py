from datetime import date, datetime
from decimal import Decimal

import pytest

from tontine.contributions import ContributionCycle, ContributionStatus
from tontine.exceptions import DuplicateContributionError


@pytest.fixture
def open_cycle() -> ContributionCycle:
    cycle = ContributionCycle(
        cycle_id="2027-01",
        start_date=date(2027, 1, 1),
        due_date=date(2027, 1, 15),
        timezone="Africa/Lagos",
    )
    cycle.add_expected_contribution("member-1", Decimal("30000"))
    return cycle


def test_cycle_classifies_paid_partial_late_and_missed_contributions(
    open_cycle: ContributionCycle,
) -> None:
    paid = open_cycle.record_contribution(
        "member-1",
        Decimal("30000"),
        payment_date=datetime.fromisoformat("2027-01-15T12:00:00+01:00"),
    )
    assert paid.status is ContributionStatus.PAID

    adjusted = open_cycle.record_contribution(
        "member-1",
        Decimal("29000"),
        payment_date=datetime.fromisoformat("2027-01-16T12:00:00+01:00"),
        adjustment=True,
    )
    assert adjusted.status is ContributionStatus.PARTIAL

    late = open_cycle.record_contribution(
        "member-1",
        Decimal("30000"),
        payment_date=datetime.fromisoformat("2027-01-16T12:00:00+01:00"),
        adjustment=True,
    )
    assert late.status is ContributionStatus.LATE

    missed = open_cycle.record_contribution(
        "member-1",
        None,
        as_of=datetime.fromisoformat("2027-01-17T12:00:00+01:00"),
        adjustment=True,
    )
    assert missed.status is ContributionStatus.MISSED


def test_cycle_reports_pending_and_decimal_totals() -> None:
    cycle = ContributionCycle(
        cycle_id="2027-01",
        start_date=date(2027, 1, 1),
        due_date=date(2027, 1, 15),
        timezone="UTC",
    )
    cycle.add_expected_contribution("member-1", "30000.10")
    cycle.add_expected_contribution("member-2", "30000.20")

    pending = cycle.record_contribution(
        "member-1",
        None,
        as_of=datetime.fromisoformat("2027-01-10T12:00:00+00:00"),
    )

    assert pending.status is ContributionStatus.PENDING
    assert cycle.expected_total == Decimal("60000.30")
    assert cycle.received_total == Decimal("0")
    assert cycle.outstanding_total == Decimal("60000.30")


def test_cycle_rejects_duplicate_records_without_explicit_adjustment(
    open_cycle: ContributionCycle,
) -> None:
    open_cycle.record_contribution(
        "member-1",
        Decimal("30000"),
        payment_date=datetime.fromisoformat("2027-01-15T12:00:00+01:00"),
    )

    with pytest.raises(DuplicateContributionError):
        open_cycle.record_contribution("member-1", Decimal("30000"))
