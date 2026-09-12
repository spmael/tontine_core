"""Contribution rules, cycles, and ledger-independent contribution records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from tontine.exceptions import DuplicateContributionError
from tontine.groups import CurrencyCode


class ContributionFrequency(StrEnum):
    """Supported contribution recurrence choices."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class DueDateConvention(StrEnum):
    """Conventions used to interpret a rule's due date."""

    EVERY_DAY = "every_day"
    WEEKDAY = "weekday"
    DAY_OF_MONTH = "day_of_month"


class CycleStatus(StrEnum):
    """Lifecycle states for a contribution cycle."""

    SCHEDULED = "scheduled"
    OPEN = "open"
    DUE = "due"
    CLOSED = "closed"


class ContributionStatus(StrEnum):
    """Derived states for a member's contribution in a cycle."""

    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    LATE = "late"
    MISSED = "missed"


def _decimal_amount(value: Decimal | int | str) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Contribution amount must be a valid decimal.") from exc
    if not amount.is_finite():
        raise ValueError("Contribution amount must be finite.")
    if amount < 0:
        raise ValueError("Contribution amount must be non-negative.")
    return amount


def _zone_info(value: str) -> ZoneInfo:
    try:
        return ZoneInfo(value)
    except (TypeError, ZoneInfoNotFoundError) as exc:
        raise ValueError(f"Unknown IANA timezone: {value!r}.") from exc


def _local_date(value: datetime, timezone: str) -> date:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Contribution timestamps must be timezone-aware.")
    return value.astimezone(_zone_info(timezone)).date()


@dataclass(frozen=True)
class ContributionRule:
    """Define a recurring Decimal amount and local due-date convention.

    The timezone is an IANA name used to interpret cycle dates. Supported
    frequencies are daily, weekly, and monthly.
    """

    amount: Decimal
    currency: CurrencyCode
    frequency: ContributionFrequency
    due_date_convention: DueDateConvention
    grace_period_days: int
    effective_date: date
    timezone: str
    due_day: int | None = None
    late_penalty: Decimal | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", _decimal_amount(self.amount))
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        object.__setattr__(self, "frequency", ContributionFrequency(self.frequency))
        _zone_info(self.timezone)
        object.__setattr__(
            self,
            "due_date_convention",
            DueDateConvention(self.due_date_convention),
        )
        if self.grace_period_days < 0:
            raise ValueError("Grace period cannot be negative.")
        if self.late_penalty is not None:
            object.__setattr__(self, "late_penalty", _decimal_amount(self.late_penalty))
        self._validate_due_convention()

    def _validate_due_convention(self) -> None:
        expected = {
            ContributionFrequency.DAILY: DueDateConvention.EVERY_DAY,
            ContributionFrequency.WEEKLY: DueDateConvention.WEEKDAY,
            ContributionFrequency.MONTHLY: DueDateConvention.DAY_OF_MONTH,
        }[self.frequency]
        if self.due_date_convention is not expected:
            raise ValueError(
                f"{self.frequency.value} contributions require the "
                f"{expected.value} due-date convention."
            )
        if self.frequency is ContributionFrequency.DAILY:
            if self.due_day is not None:
                raise ValueError("Daily contributions do not accept a due day.")
        elif self.due_day is None:
            raise ValueError(f"{self.frequency.value} contributions require a due day.")
        elif self.frequency is ContributionFrequency.WEEKLY and not (
            0 <= self.due_day <= 6
        ):
            raise ValueError("Weekly due day must be a weekday from 0 through 6.")
        elif self.frequency is ContributionFrequency.MONTHLY and not (
            1 <= self.due_day <= 28
        ):
            raise ValueError("Monthly due day must be between 1 and 28.")


@dataclass(frozen=True)
class Contribution:
    """Record one member contribution without initiating payment."""

    member_id: str
    cycle_id: str
    expected_amount: Decimal
    actual_amount: Decimal | None
    payment_date: datetime | None
    status: ContributionStatus
    external_reference: str | None = None
    notes: str | None = None


@dataclass
class ContributionCycle:
    """Track expected and recorded contributions for one contribution period."""

    cycle_id: str
    start_date: date
    due_date: date
    timezone: str
    status: CycleStatus = CycleStatus.SCHEDULED
    expected_contributions: dict[str, Decimal] = field(default_factory=dict)
    recorded_contributions: dict[str, Contribution] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.cycle_id.strip():
            raise ValueError("Cycle identifier is required.")
        _zone_info(self.timezone)
        self.status = CycleStatus(self.status)

    def add_expected_contribution(
        self,
        member_id: str,
        amount: Decimal | int | str,
    ) -> None:
        """Add one member's expected amount in the cycle currency units.

        Args:
            member_id: Identifier of the member expected to contribute.
            amount: Non-negative amount accepted by ``Decimal``.

        Raises:
            ValueError: If the member is duplicated or the amount is invalid.
        """
        if not member_id.strip():
            raise ValueError("Member identifier is required.")
        if member_id in self.expected_contributions:
            raise ValueError(f"Expected contribution already exists for {member_id!r}.")
        self.expected_contributions[member_id] = _decimal_amount(amount)

    @property
    def expected_total(self) -> Decimal:
        """Return the total expected amount in the cycle currency units."""
        return sum(self.expected_contributions.values(), Decimal("0"))

    @property
    def received_total(self) -> Decimal:
        """Return the total amount recorded as received."""
        return sum(
            (
                record.actual_amount or Decimal("0")
                for record in self.recorded_contributions.values()
            ),
            Decimal("0"),
        )

    @property
    def outstanding_total(self) -> Decimal:
        """Return expected less received, never below zero."""
        return max(self.expected_total - self.received_total, Decimal("0"))

    def record_contribution(
        self,
        member_id: str,
        actual_amount: Decimal | int | str | None,
        payment_date: datetime | None = None,
        as_of: datetime | None = None,
        external_reference: str | None = None,
        notes: str | None = None,
        adjustment: bool = False,
    ) -> Contribution:
        """Record a contribution without initiating an external payment.

        Args:
            member_id: Member whose expected contribution is being recorded.
            actual_amount: Received amount in the cycle currency units, or None.
            payment_date: Timezone-aware payment timestamp.
            as_of: Timezone-aware timestamp used for pending or missed status.
            adjustment: Replace an existing record when explicitly enabled.

        Returns:
            The recorded contribution with its derived status.

        Raises:
            DuplicateContributionError: If a record exists without adjustment.
            ValueError: If the member, amount, or timestamp is invalid.
        """
        if member_id not in self.expected_contributions:
            raise ValueError(f"No expected contribution exists for {member_id!r}.")
        if member_id in self.recorded_contributions and not adjustment:
            raise DuplicateContributionError(
                f"Contribution for {member_id!r} already exists in "
                f"cycle {self.cycle_id!r}."
            )
        expected = self.expected_contributions[member_id]
        actual = None if actual_amount is None else _decimal_amount(actual_amount)
        reference_date = as_of or payment_date or datetime.now().astimezone()
        status = self._derive_status(expected, actual, payment_date, reference_date)
        contribution = Contribution(
            member_id=member_id,
            cycle_id=self.cycle_id,
            expected_amount=expected,
            actual_amount=actual,
            payment_date=payment_date,
            status=status,
            external_reference=external_reference,
            notes=notes,
        )
        self.recorded_contributions[member_id] = contribution
        return contribution

    def _derive_status(
        self,
        expected: Decimal,
        actual: Decimal | None,
        payment_date: datetime | None,
        as_of: datetime,
    ) -> ContributionStatus:
        late_date = self.due_date
        payment_local_date = (
            None if payment_date is None else _local_date(payment_date, self.timezone)
        )
        as_of_local_date = _local_date(as_of, self.timezone)
        if actual is None:
            return (
                ContributionStatus.MISSED
                if as_of_local_date > late_date
                else ContributionStatus.PENDING
            )
        if actual < expected:
            return ContributionStatus.PARTIAL
        if payment_local_date is not None and payment_local_date > late_date:
            return ContributionStatus.LATE
        return ContributionStatus.PAID


__all__ = [
    "Contribution",
    "ContributionCycle",
    "ContributionFrequency",
    "ContributionRule",
    "ContributionStatus",
    "CycleStatus",
    "DueDateConvention",
]
