from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

import tontine
from tontine.classic import ClassicRotation
from tontine.contributions import (
    ContributionFrequency,
    ContributionRule,
    DueDateConvention,
    PenaltyDestination,
)
from tontine.investments import AllocationRule
from tontine.ledger import EntryDirection, JournalEntry, LedgerEntry
from tontine.reporting import InvestmentSummary, build_member_statement


def test_public_api_creates_group_and_cycle_without_infrastructure() -> None:
    group = tontine.create_group("group-1", "Community Circle", "JPY", "CM")
    cycle = tontine.create_contribution_cycle(
        "2027-01", date(2027, 1, 1), date(2027, 1, 31), "Asia/Tokyo"
    )

    assert group.base_currency == "JPY"
    assert group.jurisdiction == "CM"
    assert cycle.cycle_id == "2027-01"


@pytest.mark.parametrize("destination", list(PenaltyDestination))
def test_public_api_applies_rule_penalty_destination(
    destination: PenaltyDestination,
) -> None:
    rule = ContributionRule(
        amount=Decimal("100"),
        currency="JPY",
        frequency=ContributionFrequency.WEEKLY,
        due_date_convention=DueDateConvention.WEEKDAY,
        due_day=0,
        grace_period_days=0,
        effective_date=date(2027, 1, 1),
        timezone="UTC",
        late_penalty=Decimal("5"),
        penalty_destination=destination,
    )
    cycle = tontine.create_contribution_cycle(
        "2027-01",
        date(2027, 1, 1),
        date(2027, 1, 7),
        "UTC",
        rule=rule,
    )
    cycle.add_expected_contribution("member-1", rule.amount)
    cycle.add_expected_contribution("member-2", rule.amount)
    contribution = cycle.record_contribution(
        "member-1",
        rule.amount,
        payment_date=datetime(2027, 1, 8, tzinfo=UTC),
    )
    missed = cycle.record_contribution(
        "member-2",
        None,
        as_of=datetime(2027, 1, 8, tzinfo=UTC),
    )

    assert contribution.penalty_record is not None
    assert contribution.penalty_record.destination is destination
    assert contribution.penalty_record.amount == Decimal("5")
    assert contribution.penalty_record.currency == "JPY"
    assert missed.penalty_record is not None
    assert missed.penalty_record.destination is destination
    assert missed.penalty_record.amount == Decimal("5")
    assert missed.penalty_record.currency == "JPY"
    assert cycle.grace_period_days == rule.grace_period_days


def test_public_api_rejects_rule_timezone_mismatch() -> None:
    rule = ContributionRule(
        amount=Decimal("100"),
        currency="JPY",
        frequency=ContributionFrequency.WEEKLY,
        due_date_convention=DueDateConvention.WEEKDAY,
        due_day=0,
        grace_period_days=0,
        effective_date=date(2027, 1, 1),
        timezone="UTC",
    )

    with pytest.raises(ValueError, match="timezone must match"):
        tontine.create_contribution_cycle(
            "2027-01",
            date(2027, 1, 1),
            date(2027, 1, 7),
            "Asia/Tokyo",
            rule=rule,
        )


def test_public_api_rejects_rule_not_yet_effective_for_cycle() -> None:
    rule = ContributionRule(
        amount=Decimal("100"),
        currency="JPY",
        frequency=ContributionFrequency.WEEKLY,
        due_date_convention=DueDateConvention.WEEKDAY,
        due_day=0,
        grace_period_days=0,
        effective_date=date(2027, 1, 8),
        timezone="UTC",
    )

    with pytest.raises(ValueError, match="not effective"):
        tontine.create_contribution_cycle(
            "2027-01",
            date(2027, 1, 1),
            date(2027, 1, 7),
            "UTC",
            rule=rule,
        )


def test_public_api_keeps_classic_investment_ledger_and_reporting_boundaries() -> None:
    rotation = ClassicRotation.from_active_members(("member-a", "member-b"))
    allocation = AllocationRule({"cash": Decimal("100")})
    journal = JournalEntry(
        journal_id="journal-1",
        recorded_at=datetime(2027, 1, 1, tzinfo=UTC),
        description="Contribution",
        source_event="contribution-1",
        entries=(
            LedgerEntry("cash", EntryDirection.DEBIT, Decimal("100"), "JPY"),
            LedgerEntry("capital", EntryDirection.CREDIT, Decimal("100"), "JPY"),
        ),
    )
    statement = build_member_statement(
        "member-a",
        "Member A",
        "JPY",
        (),
        (),
        InvestmentSummary(Decimal("0"), Decimal("0"), Decimal("0"), "JPY"),
    )

    assert rotation.recipient_for_cycle(1) == "member-a"
    assert allocation.total_percentage == Decimal("100")
    assert journal.source_event == "contribution-1"
    assert statement.base_currency == "JPY"