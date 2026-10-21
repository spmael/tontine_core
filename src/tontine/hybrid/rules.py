"""Immutable hybrid contribution policies and effective-cycle schedules."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field, replace
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar

from tontine.currencies import CurrencyCode, smallest_unit
from tontine.exceptions import MissingRecordError


class PenaltyPaymentOrder(StrEnum):
    """Position of penalties when applying a partial payment."""

    PENALTY_FIRST = "penalty_first"
    PENALTY_LAST = "penalty_last"
    PRO_RATA = "pro_rata"


class ContributionPaymentOrder(StrEnum):
    """Distribution of a partial contribution; fund-first is unsupported."""

    POT_FIRST = "pot_first"
    PRO_RATA = "pro_rata"


class LegalForm(StrEnum):
    """Declared group form, not a legal or regulatory determination."""

    ASSOCIATION = "association"
    COOPERATIVE = "cooperative"
    UNREGISTERED = "unregistered"


class CatchUpOutcome(StrEnum):
    """Default outcome after a missed fund share's election deadline."""

    FORFEIT = "forfeit"


def _integer(value: int, label: str, minimum: int, maximum: int | None = None) -> None:
    if type(value) is not int:
        raise TypeError(f"{label} must be an integer.")
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{label} is outside its permitted range.")


def _boolean(value: bool, label: str) -> None:
    if type(value) is not bool:
        raise TypeError(f"{label} must be a boolean.")


def _decimal(value: Decimal, label: str) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{label} must be a Decimal.")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite.")


@dataclass(frozen=True)
class CatchUpPolicy:
    """Group-controlled elections, with a deadline measured in whole cycles."""

    allowed: bool = True
    deadline_cycles: int = 1
    default_outcome: CatchUpOutcome = CatchUpOutcome.FORFEIT

    def __post_init__(self) -> None:
        _boolean(self.allowed, "Catch-up allowed")
        _integer(self.deadline_cycles, "Catch-up deadline", 1)
        object.__setattr__(
            self, "default_outcome", CatchUpOutcome(self.default_outcome)
        )


@dataclass(frozen=True)
class ExitFeeSchedule:
    """Percentages of gross unit value, uniform across all units.

    Fees go to the fund. Death is always fee-free; confiscatory 100% fees are
    unsupported. Application and request-time resolution belong to exit handling.
    """

    voluntary: Decimal = Decimal("0")
    expulsion: Decimal = Decimal("0")
    death: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        for label, value in (
            ("Voluntary exit fee", self.voluntary),
            ("Expulsion exit fee", self.expulsion),
            ("Death exit fee", self.death),
        ):
            _decimal(value, label)
            if not Decimal("0") <= value < Decimal("100"):
                raise ValueError(f"{label} must be at least 0 and below 100 percent.")
        if self.death != 0:
            raise ValueError("Death exit fee must be zero.")


@dataclass(frozen=True)
class StatuteFlags:
    """Recorded statute facts; they do not determine accounting classification."""

    unconditional_redemption_refusal: bool = False
    pro_rata_wind_up: bool = False
    uniform_fee_schedule: bool = True

    def __post_init__(self) -> None:
        _boolean(self.unconditional_redemption_refusal, "Redemption refusal")
        _boolean(self.pro_rata_wind_up, "Pro-rata wind-up")
        _boolean(self.uniform_fee_schedule, "Uniform fee schedule")
        if not self.uniform_fee_schedule:
            raise ValueError("Hybrid rules require one fee schedule for all units.")


@dataclass(frozen=True)
class PayoutDeferralPolicy:
    """Cycle-end payout subject to a default maximum of 12 calendar months.

    An approved, reasoned exit-specific extension may reach the absolute
    24-month ceiling; rule configuration cannot pre-authorize it. Deadline
    calculation and extension decisions belong to exit handling.
    """

    HARD_MAX_MONTHS: ClassVar[int] = 24
    at_cycle_end: bool = True
    max_months: int = 12

    def __post_init__(self) -> None:
        _boolean(self.at_cycle_end, "Cycle-end deferral")
        _integer(self.max_months, "Default payout deferral in months", 1, 12)


@dataclass(frozen=True)
class HybridRule:
    """Hybrid policies in an explicit currency, without allocating any money.

    ``fund_share_bps`` is an integer share out of 10,000. ``launch_unit_price``
    is a positive Decimal in currency units per investment unit; no rounding is
    performed. ``max_valuation_age_days`` measures elapsed days.
    """

    currency: str
    fund_share_bps: int
    launch_unit_price: Decimal
    max_valuation_age_days: int
    penalty_order: PenaltyPaymentOrder = PenaltyPaymentOrder.PENALTY_FIRST
    contribution_order: ContributionPaymentOrder = ContributionPaymentOrder.POT_FIRST
    catch_up: CatchUpPolicy = field(default_factory=CatchUpPolicy)
    exit_fees: ExitFeeSchedule = field(default_factory=ExitFeeSchedule)
    legal_form: LegalForm = LegalForm.UNREGISTERED
    statute_flags: StatuteFlags = field(default_factory=StatuteFlags)
    payout_deferral: PayoutDeferralPolicy = field(default_factory=PayoutDeferralPolicy)

    def __post_init__(self) -> None:
        currency = CurrencyCode(self.currency)
        if smallest_unit(currency) is None:
            raise ValueError("Hybrid rules require a currency with an ISO minor unit.")
        object.__setattr__(self, "currency", currency)
        _integer(self.fund_share_bps, "Fund share in basis points", 0, 10_000)
        _decimal(self.launch_unit_price, "Launch unit price")
        if self.launch_unit_price <= 0:
            raise ValueError("Launch unit price must be positive.")
        _integer(self.max_valuation_age_days, "Maximum valuation age in days", 0)
        object.__setattr__(
            self, "penalty_order", PenaltyPaymentOrder(self.penalty_order)
        )
        object.__setattr__(
            self,
            "contribution_order",
            ContributionPaymentOrder(self.contribution_order),
        )
        object.__setattr__(self, "legal_form", LegalForm(self.legal_form))
        for value, expected in (
            (self.catch_up, CatchUpPolicy),
            (self.exit_fees, ExitFeeSchedule),
            (self.statute_flags, StatuteFlags),
            (self.payout_deferral, PayoutDeferralPolicy),
        ):
            if not isinstance(value, expected):
                raise TypeError(f"Hybrid rules require {expected.__name__}.")
        if self.exit_fees.expulsion > self.exit_fees.voluntary:
            message = "Expulsion fee exceeds the voluntary-exit fee."
            if self.legal_form is LegalForm.COOPERATIVE:
                raise ValueError(message)
            warnings.warn(message, UserWarning, stacklevel=2)


@dataclass(frozen=True)
class HybridRuleVersion:
    """Immutable version adopted before its positive effective cycle.

    Cycle zero denotes setup before the first contribution cycle. A governance
    reference records provenance, not proof that approval was valid.
    """

    version: int
    effective_cycle: int
    adopted_cycle: int
    rule: HybridRule
    governance_decision_ref: str | None = None

    def __post_init__(self) -> None:
        _integer(self.version, "Hybrid rule version", 1)
        _integer(self.effective_cycle, "Effective cycle", 1)
        _integer(self.adopted_cycle, "Adoption cycle", 0)
        if self.effective_cycle <= self.adopted_cycle:
            raise ValueError(
                "Hybrid rules must take effect after their adoption cycle."
            )
        if not isinstance(self.rule, HybridRule):
            raise TypeError("Hybrid rule versions require a HybridRule.")
        if (
            self.governance_decision_ref is not None
            and not self.governance_decision_ref.strip()
        ):
            raise ValueError("Governance decision reference must not be blank.")


@dataclass(frozen=True)
class HybridRuleSchedule:
    """One group's immutable history, latest effective cycle then version wins.

    ``group_id`` owns the schedule; version numbers are unique within it.
    Construction restores recorded history. Use ``with_version`` for additions
    so the caller's current cycle guards against retroactive changes.
    """

    group_id: str
    versions: tuple[HybridRuleVersion, ...]

    def __post_init__(self) -> None:
        if not self.group_id.strip() or any(c.isspace() for c in self.group_id):
            raise ValueError(
                "A nonblank group identifier without whitespace is required."
            )
        versions = tuple(self.versions)
        if not versions:
            raise ValueError("A hybrid schedule requires at least one version.")
        if any(not isinstance(item, HybridRuleVersion) for item in versions):
            raise TypeError("Hybrid schedules require HybridRuleVersion values.")
        if len({item.version for item in versions}) != len(versions):
            raise ValueError("Hybrid rule version numbers must be unique.")
        if len({item.rule.currency for item in versions}) != 1:
            raise ValueError("Hybrid schedule currency must not change.")
        versions = tuple(
            sorted(versions, key=lambda item: (item.effective_cycle, item.version))
        )
        for previous, current in zip(versions, versions[1:]):
            if (
                previous.rule.exit_fees != current.rule.exit_fees
                and current.effective_cycle < current.adopted_cycle + 2
            ):
                raise ValueError(
                    "Fee changes require at least one full cycle of notice."
                )
        object.__setattr__(self, "versions", versions)

    def with_version(
        self, version: HybridRuleVersion, *, current_cycle: int
    ) -> HybridRuleSchedule:
        """Return an extended schedule without changing historical resolutions.

        Args:
            version: New version, including its recorded adoption cycle.
            current_cycle: Caller-supplied current cycle, or zero during setup.

        Raises:
            ValueError: For duplicate versions, retroactivity, currency changes,
                or insufficient fee-change notice.
        """
        _integer(current_cycle, "Current cycle", 0)
        if not isinstance(version, HybridRuleVersion):
            raise TypeError("Expected a HybridRuleVersion.")
        if version.effective_cycle <= current_cycle:
            raise ValueError("Effective cycle must be after the current cycle.")
        if version.adopted_cycle > current_cycle:
            raise ValueError("Adoption cycle must not be in the future.")
        applicable = [
            item
            for item in self.versions
            if item.effective_cycle <= version.effective_cycle
        ]
        previous = applicable[-1] if applicable else self.versions[0]
        if (
            previous.rule.exit_fees != version.rule.exit_fees
            and version.effective_cycle < version.adopted_cycle + 2
        ):
            raise ValueError("Fee changes require at least one full cycle of notice.")
        return replace(self, versions=(*self.versions, version))

    def version_for_cycle(self, cycle_number: int) -> HybridRuleVersion:
        """Resolve the latest effective cycle, with highest version breaking ties.

        Raises:
            ValueError: If the cycle is not a positive integer.
            MissingRecordError: If no version is effective.
        """
        _integer(cycle_number, "Hybrid cycle", 1)
        applicable = [
            item for item in self.versions if item.effective_cycle <= cycle_number
        ]
        if not applicable:
            raise MissingRecordError(
                f"No hybrid rule is effective for cycle {cycle_number}."
            )
        return applicable[-1]
