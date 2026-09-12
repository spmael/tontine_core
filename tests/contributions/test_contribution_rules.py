from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from tontine.contributions import (
    ContributionCycle,
    ContributionFrequency,
    ContributionRule,
    CycleStatus,
    DueDateConvention,
)


def test_weekly_jpy_rule_uses_weekday_convention() -> None:
    rule = ContributionRule(
        amount=Decimal("30000"),
        currency="JPY",
        frequency=ContributionFrequency.WEEKLY,
        due_date_convention=DueDateConvention.WEEKDAY,
        due_day=0,
        grace_period_days=2,
        effective_date=date(2027, 1, 1),
        timezone="Asia/Tokyo",
    )

    assert rule.amount == Decimal("30000")
    assert rule.frequency is ContributionFrequency.WEEKLY
    assert rule.due_day == 0


def test_daily_jpy_rule_uses_every_day_convention() -> None:
    rule = ContributionRule(
        amount=Decimal("30000"),
        currency="JPY",
        frequency="daily",
        due_date_convention="every_day",
        grace_period_days=0,
        effective_date=date(2027, 1, 1),
        timezone="Africa/Lagos",
    )

    assert rule.frequency is ContributionFrequency.DAILY
    assert rule.due_date_convention is DueDateConvention.EVERY_DAY


def test_monthly_jpy_rule_uses_day_of_month_convention() -> None:
    rule = ContributionRule(
        amount="30000",
        currency="JPY",
        frequency="monthly",
        due_date_convention="day_of_month",
        due_day=15,
        grace_period_days=5,
        effective_date=date(2027, 1, 1),
        timezone="Asia/Tokyo",
    )

    assert rule.frequency is ContributionFrequency.MONTHLY
    assert rule.due_date_convention is DueDateConvention.DAY_OF_MONTH


def test_rule_rejects_negative_amount_and_invalid_frequency_convention() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        ContributionRule(
            amount=Decimal("-1"),
            currency="JPY",
            frequency="weekly",
            due_date_convention="weekday",
            due_day=0,
            grace_period_days=0,
            effective_date=date(2027, 1, 1),
            timezone="UTC",
        )

    with pytest.raises(ValueError, match="day_of_month"):
        ContributionRule(
            amount=Decimal("30000"),
            currency="JPY",
            frequency="monthly",
            due_date_convention="weekday",
            due_day=0,
            grace_period_days=0,
            effective_date=date(2027, 1, 1),
            timezone="UTC",
        )


def test_cycle_has_explicit_status_due_date_and_expected_contributions() -> None:
    cycle = ContributionCycle(
        cycle_id="2027-W01",
        start_date=date(2027, 1, 1),
        due_date=date(2027, 1, 7),
        timezone="America/New_York",
        status=CycleStatus.OPEN,
    )
    cycle.add_expected_contribution("member-1", Decimal("30000"))

    assert cycle.status is CycleStatus.OPEN
    assert cycle.due_date == date(2027, 1, 7)
    assert cycle.expected_contributions == {"member-1": Decimal("30000")}
    assert cycle.expected_total == Decimal("30000")


def test_payment_status_uses_cycle_timezone_for_local_due_date() -> None:
    cycle = ContributionCycle(
        cycle_id="2027-W01",
        start_date=date(2027, 1, 1),
        due_date=date(2027, 1, 7),
        timezone="America/New_York",
    )
    cycle.add_expected_contribution("member-1", Decimal("30000"))

    contribution = cycle.record_contribution(
        member_id="member-1",
        actual_amount=Decimal("30000"),
        payment_date=datetime(2027, 1, 8, 0, 30, tzinfo=UTC),
    )

    assert contribution.status.value == "paid"
