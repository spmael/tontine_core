"""Contribution rules, cycles, and ledger-independent contribution records."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from tontine._datetime import require_aware_datetime
from tontine.exceptions import DuplicateContributionError, MissingRecordError
from tontine.groups import CurrencyCode

if TYPE_CHECKING:
    from tontine.members import ParticipationShare


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


class PenaltyReason(StrEnum):
    """Reasons supported for automatically assessed contribution penalties."""

    LATE_CONTRIBUTION = "late_contribution"
    MISSED_CONTRIBUTION = "missed_contribution"


class PenaltyStatus(StrEnum):
    """Lifecycle state of an assessed penalty."""

    UNPAID = "unpaid"


class PenaltyDestination(StrEnum):
    """Group destination assigned to assessed penalty money."""

    COMMON_RESERVE = "common_reserve"
    DISTRIBUTE_AT_CYCLE_END = "distribute_at_cycle_end"
    SOCIAL_FUND = "social_fund"
    COMPENSATE_AFFECTED_MEMBER = "compensate_affected_member"
    ADMINISTRATION_FUND = "administration_fund"
    ROTATION_POT = "rotation_pot"


def _decimal_amount(
    value: Decimal | int | str,
    label: str = "Contribution amount",
) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} must be a valid decimal.") from exc
    if not amount.is_finite():
        raise ValueError(f"{label} must be finite.")
    if amount < 0:
        raise ValueError(f"{label} must be non-negative.")
    return amount


def _zone_info(value: str) -> ZoneInfo:
    try:
        return ZoneInfo(value)
    except (TypeError, ZoneInfoNotFoundError) as exc:
        raise ValueError(f"Unknown IANA timezone: {value!r}.") from exc


def _local_date(value: datetime, timezone: str, field_name: str) -> date:
    require_aware_datetime(value, field_name)
    return value.astimezone(_zone_info(timezone)).date()


@dataclass(frozen=True)
class ContributionRule:
    """Define a recurring Decimal amount and local due-date convention.

    The timezone is an IANA name used to interpret cycle dates. Supported
    frequencies are daily, weekly, and monthly. Penalty destinations default
    to the common reserve.
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
    penalty_destination: PenaltyDestination = PenaltyDestination.COMMON_RESERVE

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", _decimal_amount(self.amount))
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        object.__setattr__(self, "frequency", ContributionFrequency(self.frequency))
        object.__setattr__(
            self,
            "penalty_destination",
            PenaltyDestination(self.penalty_destination),
        )
        _zone_info(self.timezone)
        object.__setattr__(
            self,
            "due_date_convention",
            DueDateConvention(self.due_date_convention),
        )
        if self.grace_period_days < 0:
            raise ValueError("Grace period cannot be negative.")
        if self.late_penalty is not None:
            object.__setattr__(
                self,
                "late_penalty",
                _decimal_amount(self.late_penalty, "Late penalty"),
            )
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
class Penalty:
    """Immutable penalty assessment kept separate from a contribution amount.

    ``assessed_on`` must be timezone-aware; construct it with
    ``datetime.timezone.utc`` or ``zoneinfo.ZoneInfo``.
    """

    member_id: str
    cycle_id: str
    reason: PenaltyReason
    amount: Decimal
    currency: CurrencyCode
    assessed_on: datetime
    status: PenaltyStatus = PenaltyStatus.UNPAID
    destination: PenaltyDestination = PenaltyDestination.COMMON_RESERVE

    def __post_init__(self) -> None:
        if not self.member_id.strip() or not self.cycle_id.strip():
            raise ValueError("Penalty member and cycle identifiers are required.")
        object.__setattr__(self, "reason", PenaltyReason(self.reason))
        object.__setattr__(self, "status", PenaltyStatus(self.status))
        object.__setattr__(self, "destination", PenaltyDestination(self.destination))
        object.__setattr__(self, "amount", _decimal_amount(self.amount, "Penalty"))
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        require_aware_datetime(self.assessed_on, "assessed_on")

    @property
    def assessment_id(self) -> str:
        """Return a stable identifier for this member's cycle penalty assessment."""
        identity = json.dumps(
            [self.cycle_id, self.member_id, self.reason.value],
            ensure_ascii=True,
            separators=(",", ":"),
        )
        return f"penalty:{identity}"


@dataclass(frozen=True)
class Contribution:
    """Record one member contribution without initiating payment.

    If provided, ``payment_date`` must be timezone-aware; construct it with
    ``datetime.timezone.utc`` or ``zoneinfo.ZoneInfo``.
    """

    member_id: str
    cycle_id: str
    expected_amount: Decimal
    actual_amount: Decimal | None
    payment_date: datetime | None
    status: ContributionStatus
    external_reference: str | None = None
    notes: str | None = None
    penalty: Decimal = Decimal("0")
    penalty_record: Penalty | None = None

    def __post_init__(self) -> None:
        if self.payment_date is not None:
            require_aware_datetime(self.payment_date, "payment_date")

    @property
    def participant_id(self) -> str:
        """Return the member or share identifier used as the cycle key."""
        return self.member_id


@dataclass(frozen=True)
class ShareContribution:
    """Contribution record paired with its share and owning member identity."""

    share_id: str
    member_id: str
    contribution: Contribution

    def __post_init__(self) -> None:
        if not self.share_id.strip() or not self.member_id.strip():
            raise ValueError("Share contribution identities are required.")
        if self.contribution.participant_id != self.share_id:
            raise ValueError("Contribution participant must match the share ID.")


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
    grace_period_days: int = 0
    late_penalty: Decimal = Decimal("0")
    penalty_currency: CurrencyCode | None = None
    penalty_destination: PenaltyDestination = PenaltyDestination.COMMON_RESERVE

    def __post_init__(self) -> None:
        if not self.cycle_id.strip():
            raise ValueError("Cycle identifier is required.")
        _zone_info(self.timezone)
        self.status = CycleStatus(self.status)
        self.penalty_destination = PenaltyDestination(self.penalty_destination)
        if self.grace_period_days < 0:
            raise ValueError("Grace period cannot be negative.")
        self.late_penalty = _decimal_amount(self.late_penalty, "Late penalty")
        if self.penalty_currency is not None:
            self.penalty_currency = CurrencyCode(str(self.penalty_currency))
        if self.late_penalty != 0 and self.penalty_currency is None:
            raise ValueError(
                "Penalty currency is required when a late penalty is configured."
            )

    @classmethod
    def from_rule(
        cls,
        cycle_id: str,
        start_date: date,
        due_date: date,
        rule: ContributionRule,
    ) -> ContributionCycle:
        """Create a cycle using the applicable contribution rule's settings.

        Args:
            cycle_id: Unique identifier for the contribution period.
            start_date: First date covered by the cycle.
            due_date: Date on which contributions are due.
            rule: Rule effective on the cycle start date.

        Raises:
            ValueError: If the rule is not effective by the cycle start date.
        """
        if rule.effective_date > start_date:
            raise ValueError(
                "Contribution rule is not effective for the cycle start date."
            )
        return cls(
            cycle_id=cycle_id,
            start_date=start_date,
            due_date=due_date,
            timezone=rule.timezone,
            grace_period_days=rule.grace_period_days,
            late_penalty=(
                Decimal("0") if rule.late_penalty is None else rule.late_penalty
            ),
            penalty_currency=rule.currency,
            penalty_destination=rule.penalty_destination,
        )

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

    def add_expected_share_contribution(
        self,
        share: ParticipationShare,
        cycle_number: int,
        amount: Decimal | int | str,
    ) -> None:
        """Add an expected amount for a share active in the specified cycle.

        Args:
            share: Stable share record that owns this cycle contribution.
            cycle_number: One-based effective cycle for the contribution.
            amount: Non-negative amount in the contribution cycle currency units.

        Raises:
            ValueError: If the share is inactive, duplicated, or the amount is
                invalid.
        """
        if not share.is_active_for(cycle_number):
            raise ValueError(
                f"Participation share {share.share_id!r} is not active in "
                f"cycle {cycle_number}."
            )
        self.add_expected_contribution(str(share.share_id), amount)

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

    @property
    def penalties_total(self) -> Decimal:
        """Return penalties assessed for late or missed contributions."""
        return sum(
            (record.penalty for record in self.recorded_contributions.values()),
            Decimal("0"),
        )

    def penalty_for(self, member_id: str) -> Decimal:
        """Return the assessed penalty for one recorded contribution.

        Raises:
            MissingRecordError: If no contribution is recorded for the member.
        """
        try:
            return self.recorded_contributions[member_id].penalty
        except KeyError as exc:
            raise MissingRecordError(
                f"No contribution is recorded for {member_id!r}."
            ) from exc

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
            payment_date: Aware payment timestamp, constructed with
                ``datetime.timezone.utc`` or ``zoneinfo.ZoneInfo``.
            as_of: Aware status reference timestamp, constructed with
                ``datetime.timezone.utc`` or ``zoneinfo.ZoneInfo``.
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
        if payment_date is not None:
            require_aware_datetime(payment_date, "payment_date")
        if as_of is not None:
            require_aware_datetime(as_of, "as_of")
        expected = self.expected_contributions[member_id]
        actual = (
            None
            if actual_amount is None
            else _decimal_amount(actual_amount, "Contribution amount")
        )
        reference_date = as_of or payment_date or datetime.now().astimezone()
        status = self._derive_status(expected, actual, payment_date, reference_date)
        penalty, penalty_record = self._derive_penalty(
            member_id, actual, payment_date, reference_date
        )
        contribution = Contribution(
            member_id=member_id,
            cycle_id=self.cycle_id,
            expected_amount=expected,
            actual_amount=actual,
            payment_date=payment_date,
            status=status,
            external_reference=external_reference,
            notes=notes,
            penalty=penalty,
            penalty_record=penalty_record,
        )
        self.recorded_contributions[member_id] = contribution
        return contribution

    def record_share_contribution(
        self,
        share: ParticipationShare,
        cycle_number: int,
        actual_amount: Decimal | int | str | None,
        payment_date: datetime | None = None,
        as_of: datetime | None = None,
        external_reference: str | None = None,
        notes: str | None = None,
        adjustment: bool = False,
    ) -> ShareContribution:
        """Record a share contribution and retain the owning member identity.

        The share identifier is the cycle participant key; the returned wrapper
        also carries the person who owns that share for person-level reporting.

        Args:
            share: Stable share record that owns this cycle contribution.
            cycle_number: One-based effective cycle for the contribution.
            actual_amount: Received amount in cycle currency units, or ``None``.
            payment_date: Optional timezone-aware payment timestamp.
            as_of: Optional timezone-aware status reference timestamp.
            external_reference: Optional caller-supplied receipt reference.
            notes: Optional contribution note.
            adjustment: Whether to replace an existing share contribution.

        Returns:
            The contribution paired with its share and owning member IDs.

        Raises:
            DuplicateContributionError: If a record exists without adjustment.
            ValueError: If the share is inactive, expected amount is missing,
                or the contribution or timestamps are invalid.
        """
        if not share.is_active_for(cycle_number):
            raise ValueError(
                f"Participation share {share.share_id!r} is not active in "
                f"cycle {cycle_number}."
            )
        record = self.record_contribution(
            str(share.share_id),
            actual_amount,
            payment_date,
            as_of,
            external_reference,
            notes,
            adjustment,
        )
        return ShareContribution(
            share_id=str(share.share_id),
            member_id=str(share.member_id),
            contribution=record,
        )

    def _derive_status(
        self,
        expected: Decimal,
        actual: Decimal | None,
        payment_date: datetime | None,
        as_of: datetime,
    ) -> ContributionStatus:
        late_date = self.due_date + timedelta(days=self.grace_period_days)
        payment_local_date = (
            None
            if payment_date is None
            else _local_date(payment_date, self.timezone, "payment_date")
        )
        as_of_local_date = _local_date(as_of, self.timezone, "as_of")
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

    def _derive_penalty(
        self,
        member_id: str,
        actual: Decimal | None,
        payment_date: datetime | None,
        as_of: datetime,
    ) -> tuple[Decimal, Penalty | None]:
        threshold = self.due_date + timedelta(days=self.grace_period_days)
        payment_local_date = (
            None
            if payment_date is None
            else _local_date(payment_date, self.timezone, "payment_date")
        )
        late = (payment_local_date is not None and payment_local_date > threshold) or (
            actual is None and _local_date(as_of, self.timezone, "as_of") > threshold
        )
        if not late or self.late_penalty == 0:
            return Decimal("0"), None
        assert self.penalty_currency is not None
        reason = (
            PenaltyReason.MISSED_CONTRIBUTION
            if actual is None
            else PenaltyReason.LATE_CONTRIBUTION
        )
        penalty = Penalty(
            member_id=member_id,
            cycle_id=self.cycle_id,
            reason=reason,
            amount=self.late_penalty,
            currency=self.penalty_currency,
            assessed_on=payment_date or as_of,
            destination=self.penalty_destination,
        )
        return penalty.amount, penalty


__all__ = [
    "Contribution",
    "ContributionCycle",
    "ContributionFrequency",
    "Penalty",
    "PenaltyDestination",
    "PenaltyReason",
    "PenaltyStatus",
    "ContributionRule",
    "ContributionStatus",
    "CycleStatus",
    "DueDateConvention",
    "ShareContribution",
]
