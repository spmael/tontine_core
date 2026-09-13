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


def test_cycle_assesses_fixed_penalties_after_grace_period() -> None:
    cycle = ContributionCycle(
        cycle_id="2027-02",
        start_date=date(2027, 2, 1),
        due_date=date(2027, 2, 15),
        timezone="UTC",
        grace_period_days=2,
        late_penalty=Decimal("50"),
        penalty_currency="JPY",
    )
    cycle.add_expected_contribution("member-paid", Decimal("100"))
    cycle.add_expected_contribution("member-late", Decimal("100"))
    cycle.add_expected_contribution("member-missed", Decimal("100"))

    paid = cycle.record_contribution(
        "member-paid",
        Decimal("100"),
        payment_date=datetime.fromisoformat("2027-02-17T10:00:00+00:00"),
    )
    late = cycle.record_contribution(
        "member-late",
        Decimal("100"),
        payment_date=datetime.fromisoformat("2027-02-18T10:00:00+00:00"),
    )
    missed = cycle.record_contribution(
        "member-missed",
        None,
        as_of=datetime.fromisoformat("2027-02-18T10:00:00+00:00"),
    )

    assert paid.status is ContributionStatus.PAID
    assert paid.penalty == Decimal("0")
    assert late.status is ContributionStatus.LATE
    assert late.penalty == Decimal("50")
    assert late.penalty_record is not None
    assert late.penalty_record.currency == "JPY"
    assert late.penalty_record.reason.value == "late_contribution"
    assert late.penalty_record.status.value == "unpaid"
    assert late.penalty_record.destination.value == "common_reserve"
    assert missed.status is ContributionStatus.MISSED
    assert missed.penalty == Decimal("50")
    assert missed.penalty_record is not None
    assert missed.penalty_record.reason.value == "missed_contribution"
    assert cycle.penalties_total == Decimal("100")
    assert cycle.penalty_for("member-late") == Decimal("50")

    adjusted = cycle.record_contribution(
        "member-late",
        Decimal("100"),
        payment_date=datetime.fromisoformat("2027-02-16T10:00:00+00:00"),
        adjustment=True,
    )
    assert adjusted.penalty == Decimal("0")
    assert cycle.penalties_total == Decimal("50")

    with pytest.raises(KeyError, match="No contribution"):
        cycle.penalty_for("unknown")
