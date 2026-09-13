"""Investment allocation, valuation, and supplied FX-rate vocabulary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Protocol

from tontine.audit import AuditEventRegistry
from tontine.currencies import CurrencyCode
from tontine.exceptions import DuplicateInvestmentEventError


def _decimal_value(value: Decimal | int | str, label: str) -> Decimal:
    if isinstance(value, float) or not isinstance(value, (Decimal, int, str)):
        raise TypeError(f"{label} must use Decimal-compatible values.")
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} must be a valid decimal.") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{label} must be finite.")
    return decimal_value


def _non_negative(value: Decimal | int | str, label: str) -> Decimal:
    decimal_value = _decimal_value(value, label)
    if decimal_value < 0:
        raise ValueError(f"{label} must be non-negative.")
    return decimal_value


class AssetCategory(StrEnum):
    """Configurable categories for investment assets."""

    CASH = "cash"
    BOND = "bond"
    EQUITY = "equity"
    FUND = "fund"
    REAL_ESTATE = "real_estate"
    OTHER = "other"


@dataclass(frozen=True)
class AllocationRule:
    """Define allocation percentages without hard-coding investment choices."""

    categories: dict[str, Decimal]

    def __post_init__(self) -> None:
        if not self.categories:
            raise ValueError("At least one allocation category is required.")
        normalized = {
            category.strip(): _non_negative(value, "Allocation percentage")
            for category, value in self.categories.items()
        }
        if any(not category for category in normalized):
            raise ValueError("Allocation category names are required.")
        if sum(normalized.values(), Decimal("0")) != Decimal("100"):
            raise ValueError("Allocation percentages must total 100.")
        object.__setattr__(self, "categories", normalized)

    @property
    def total_percentage(self) -> Decimal:
        """Return the exact Decimal percentage total."""
        return sum(self.categories.values(), Decimal("0"))


@dataclass(frozen=True)
class ScheduledAllocationRule:
    """Immutable allocation-rule version with an effective cycle range."""

    rule_id: str
    version: int
    rule: AllocationRule
    effective_cycle: int
    end_cycle: int | None = None
    cancelled_from_cycle: int | None = None

    def applies_to(self, cycle_number: int) -> bool:
        """Return whether this rule version applies to a cycle."""
        return (
            self.effective_cycle <= cycle_number
            and (self.end_cycle is None or cycle_number <= self.end_cycle)
            and (
                self.cancelled_from_cycle is None
                or cycle_number < self.cancelled_from_cycle
            )
        )


class AllocationRuleSchedule:
    """Resolve recurring, ended, cancelled, and replaced allocation rules."""

    def __init__(self, audit_registry: AuditEventRegistry | None = None) -> None:
        self._rules: list[ScheduledAllocationRule] = []
        self._audit_registry = audit_registry

    def add_rule(
        self,
        rule_id: str,
        version: int,
        rule: AllocationRule,
        effective_cycle: int,
        end_cycle: int | None = None,
    ) -> ScheduledAllocationRule:
        """Add a recurring or bounded allocation-rule version.

        Args:
            rule_id: Stable allocation-rule identifier.
            version: Immutable rule version number.
            rule: Percentage allocation definition totaling 100 percent.
            effective_cycle: First cycle using the rule.
            end_cycle: Optional last cycle using the rule.

        Returns:
            The immutable scheduled rule.
        """
        if not rule_id.strip() or version < 1:
            raise ValueError("Allocation rule identity is invalid.")
        if effective_cycle < 1 or (
            end_cycle is not None and end_cycle < effective_cycle
        ):
            raise ValueError("Allocation rule cycle range is invalid.")
        if any(
            item.rule_id == rule_id and item.version == version
            for item in self._rules
        ):
            raise ValueError(f"Allocation rule {rule_id!r} is already registered.")
        scheduled = ScheduledAllocationRule(
            rule_id=rule_id,
            version=version,
            rule=rule,
            effective_cycle=effective_cycle,
            end_cycle=end_cycle,
        )
        self._rules.append(scheduled)
        self._record_audit("allocation_rule.added", rule_id, version)
        return scheduled

    def cancel(self, rule_id: str, from_cycle: int) -> None:
        """Stop a recurring rule from a cycle onward without mutating history.

        Args:
            rule_id: Allocation rule to stop.
            from_cycle: First cycle in which the rule no longer applies.

        Raises:
            KeyError: If the rule is not registered.
            ValueError: If the cancellation cycle is not after activation.
        """
        if from_cycle < 1:
            raise ValueError("Cancellation cycle must be positive.")
        candidates = [item for item in self._rules if item.rule_id == rule_id]
        if not candidates:
            raise KeyError(f"Allocation rule {rule_id!r} was not found.")
        current = max(candidates, key=lambda item: item.effective_cycle)
        if from_cycle <= current.effective_cycle:
            raise ValueError("Cancellation must occur after the rule effective cycle.")
        self._rules.remove(current)
        self._rules.append(
            ScheduledAllocationRule(
                rule_id=current.rule_id,
                version=current.version,
                rule=current.rule,
                effective_cycle=current.effective_cycle,
                end_cycle=current.end_cycle,
                cancelled_from_cycle=from_cycle,
            )
        )
        self._record_audit("allocation_rule.cancelled", rule_id, current.version)

    def rule_for_cycle(self, cycle_number: int) -> ScheduledAllocationRule:
        """Return the latest applicable rule version for a cycle.

        Args:
            cycle_number: Positive contribution cycle number.

        Returns:
            The latest scheduled rule effective for the cycle.

        Raises:
            KeyError: If no rule is effective for the cycle.
        """
        if cycle_number < 1:
            raise ValueError("Allocation cycle must be positive.")
        applicable = [item for item in self._rules if item.applies_to(cycle_number)]
        if not applicable:
            raise KeyError(f"No allocation rule is effective for cycle {cycle_number}.")
        return max(applicable, key=lambda item: item.effective_cycle)

    def _record_audit(self, event_type: str, rule_id: str, version: int) -> None:
        if self._audit_registry is None:
            return
        event_number = len(self._audit_registry.all_events()) + 1
        self._audit_registry.record(
            event_id=f"{event_type}:{rule_id}:{version}:{event_number}",
            event_type=event_type,
            aggregate_type="allocation_rule",
            aggregate_id=rule_id,
            occurred_at=datetime.now().astimezone(),
            actor_id=None,
            source_event=None,
            details={"version": version},
        )


@dataclass(frozen=True)
class AssetDefinition:
    """Identify an investment asset held or tracked by the group."""

    asset_id: str
    name: str
    category: AssetCategory
    currency: CurrencyCode

    def __post_init__(self) -> None:
        if not self.asset_id.strip():
            raise ValueError("Asset identifier is required.")
        if not self.name.strip():
            raise ValueError("Asset name is required.")
        object.__setattr__(self, "category", AssetCategory(self.category))
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))


@dataclass(frozen=True)
class ManualValuation:
    """Record a manually supplied asset valuation with its source."""

    asset_id: str
    value: Decimal
    currency: CurrencyCode
    effective_date: date
    source: str

    def __post_init__(self) -> None:
        if not self.asset_id.strip():
            raise ValueError("Valuation asset identifier is required.")
        if not self.source.strip():
            raise ValueError("Valuation source is required.")
        object.__setattr__(self, "value", _non_negative(self.value, "Valuation"))
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))


class InvestmentActivityType(StrEnum):
    """Recorded investment activity categories."""

    PURCHASE = "purchase"
    SALE = "sale"
    INCOME = "income"
    FEE = "fee"


@dataclass(frozen=True)
class InvestmentActivity:
    """Immutable record of investment activity without execution behavior."""

    event_id: str
    event_type: InvestmentActivityType
    asset_id: str
    amount: Decimal
    currency: CurrencyCode
    effective_date: date
    recorded_at: datetime
    source: str

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.asset_id.strip():
            raise ValueError("Investment event and asset identifiers are required.")
        if not self.source.strip():
            raise ValueError("Investment activity source is required.")
        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("Investment activity timestamps must be timezone-aware.")
        object.__setattr__(self, "event_type", InvestmentActivityType(self.event_type))
        object.__setattr__(
            self,
            "amount",
            _non_negative(self.amount, "Activity amount"),
        )
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))


class InvestmentActivityRegistry:
    """Store immutable investment activity and reject duplicate event IDs."""

    def __init__(self) -> None:
        self._activities: dict[str, InvestmentActivity] = {}

    def record_activity(
        self,
        event_id: str,
        event_type: InvestmentActivityType,
        asset: AssetDefinition,
        amount: Decimal | int | str,
        currency: str,
        effective_date: date,
        recorded_at: datetime,
        source: str,
    ) -> InvestmentActivity:
        """Record supplied investment activity without executing a transaction.

        Args:
            event_id: Unique investment-event identifier.
            event_type: Purchase, sale, income, or fee category.
            asset: Asset definition associated with the activity.
            amount: Non-negative Decimal-compatible amount.
            currency: ISO 4217 activity currency.
            effective_date: Date on which the activity occurred.
            recorded_at: Timezone-aware timestamp when it was recorded.
            source: Statement or other supplied provenance source.

        Returns:
            The immutable activity record.

        Raises:
            DuplicateInvestmentEventError: If the event ID already exists.
        """
        if event_id in self._activities:
            raise DuplicateInvestmentEventError(
                f"Investment event {event_id!r} is already recorded."
            )
        activity = InvestmentActivity(
            event_id=event_id,
            event_type=event_type,
            asset_id=asset.asset_id,
            amount=_non_negative(amount, "Activity amount"),
            currency=CurrencyCode(currency),
            effective_date=effective_date,
            recorded_at=recorded_at,
            source=source,
        )
        self._activities[event_id] = activity
        return activity


@dataclass(frozen=True)
class Liability:
    """Record a manually supplied group liability in an explicit currency."""

    liability_id: str
    amount: Decimal
    currency: CurrencyCode
    effective_date: date
    source: str

    def __post_init__(self) -> None:
        if not self.liability_id.strip():
            raise ValueError("Liability identifier is required.")
        if not self.source.strip():
            raise ValueError("Liability source is required.")
        object.__setattr__(self, "amount", _non_negative(self.amount, "Liability"))
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))


class LiabilityRegistry:
    """Aggregate immutable, manually supplied liabilities by currency."""

    def __init__(self) -> None:
        self._liabilities: dict[str, Liability] = {}

    def record(self, liability: Liability) -> None:
        """Record a liability and reject duplicate identifiers."""
        if liability.liability_id in self._liabilities:
            raise ValueError(
                f"Liability {liability.liability_id!r} is already recorded."
            )
        self._liabilities[liability.liability_id] = liability

    def total(self, currency: str) -> Decimal:
        """Return liabilities recorded in the requested currency."""
        expected_currency = CurrencyCode(currency)
        return sum(
            (
                liability.amount
                for liability in self._liabilities.values()
                if liability.currency == expected_currency
            ),
            Decimal("0"),
        )


@dataclass(frozen=True)
class InvestmentValuation:
    """Derive NAV and member values from supplied Decimal valuation inputs."""

    assets: Decimal
    liabilities: Decimal
    units_outstanding: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "assets", _non_negative(self.assets, "Assets"))
        object.__setattr__(
            self,
            "liabilities",
            _non_negative(self.liabilities, "Liabilities"),
        )
        object.__setattr__(
            self,
            "units_outstanding",
            _non_negative(self.units_outstanding, "Units outstanding"),
        )
        if self.units_outstanding == 0:
            raise ValueError("Units outstanding must be greater than zero.")

    @property
    def nav(self) -> Decimal:
        """Return net asset value as assets less liabilities."""
        return self.assets - self.liabilities

    @property
    def unit_price(self) -> Decimal:
        """Return NAV divided by units outstanding without quantization."""
        return self.nav / self.units_outstanding

    def member_value(self, units: Decimal | int | str) -> Decimal:
        """Return the attributable value for supplied member units.

        Args:
            units: Non-negative member units in the valuation's unit system.

        Returns:
            Units multiplied by the unquantized Decimal unit price.
        """
        return _non_negative(units, "Member units") * self.unit_price

    def member_ownership_percentage(self, units: Decimal | int | str) -> Decimal:
        """Return a member's percentage of total outstanding units.

        Raises:
            ValueError: If units are negative or exceed total outstanding units.
        """
        normalized_units = _non_negative(units, "Member units")
        if normalized_units > self.units_outstanding:
            raise ValueError("Member units cannot exceed total outstanding units.")
        return (
            normalized_units
            / self.units_outstanding
            * Decimal("100")
        )

    @classmethod
    def from_liabilities(
        cls,
        assets: Decimal | int | str,
        liabilities: LiabilityRegistry,
        currency: str,
        units_outstanding: Decimal | int | str,
        *,
        asset_currency: str,
    ) -> InvestmentValuation:
        """Create a valuation using liabilities aggregated from a registry."""
        if CurrencyCode(asset_currency) != CurrencyCode(currency):
            raise ValueError(
                "Asset currency must match liability aggregation currency."
            )
        return cls(
            assets=_non_negative(assets, "Assets"),
            liabilities=liabilities.total(currency),
            units_outstanding=_non_negative(units_outstanding, "Units outstanding"),
        )


class MemberUnitLedger:
    """Derive member unit balances from immutable issue and redemption events."""

    def __init__(self) -> None:
        self._balances: dict[str, Decimal] = {}
        self._event_ids: set[str] = set()

    def issue(
        self,
        member_id: str,
        contribution: Decimal | int | str,
        unit_price: Decimal | int | str,
        event_id: str,
    ) -> Decimal:
        """Issue units from a contribution amount and explicit unit price.

        Args:
            member_id: Member receiving the units.
            contribution: Non-negative contribution amount.
            unit_price: Positive Decimal unit price.
            event_id: Unique immutable unit-event identifier.

        Returns:
            The Decimal quantity issued.
        """
        self._record_event(event_id)
        amount = _non_negative(contribution, "Contribution")
        price = _non_negative(unit_price, "Unit price")
        if price == 0:
            raise ValueError("Unit price must be greater than zero.")
        units = amount / price
        self._balances[member_id] = self._balances.get(member_id, Decimal("0")) + units
        return units

    def redeem(
        self,
        member_id: str,
        units: Decimal | int | str,
        event_id: str,
    ) -> None:
        """Redeem units without mutating prior unit events.

        Args:
            member_id: Member whose units are redeemed.
            units: Non-negative units not exceeding the member balance.
            event_id: Unique immutable redemption-event identifier.

        Raises:
            ValueError: If units are invalid or exceed the member balance.
        """
        self._record_event(event_id)
        quantity = _non_negative(units, "Units")
        if quantity > self.balance_for(member_id):
            raise ValueError("Units cannot exceed the member balance.")
        self._balances[member_id] = self.balance_for(member_id) - quantity

    def balance_for(self, member_id: str) -> Decimal:
        """Return the member's derived unit balance."""
        return self._balances.get(member_id, Decimal("0"))

    @property
    def total_units(self) -> Decimal:
        """Return total outstanding units across members."""
        return sum(self._balances.values(), Decimal("0"))

    def ownership_percentage_for(self, member_id: str) -> Decimal:
        """Return a member's percentage of total outstanding units."""
        if self.total_units == 0:
            return Decimal("0")
        return self.balance_for(member_id) / self.total_units * Decimal("100")

    def ownership_percentages(self) -> dict[str, Decimal]:
        """Return ownership percentages for every member with units."""
        return {
            member_id: self.ownership_percentage_for(member_id)
            for member_id in self._balances
        }

    def _record_event(self, event_id: str) -> None:
        if not event_id.strip():
            raise ValueError("Unit event identifier is required.")
        if event_id in self._event_ids:
            raise ValueError(f"Unit event {event_id!r} is already recorded.")
        self._event_ids.add(event_id)


@dataclass(frozen=True)
class FxRate:
    """Record an externally supplied, timestamped currency-pair exchange rate."""

    base_currency: CurrencyCode
    quote_currency: CurrencyCode
    rate: Decimal
    effective_at: datetime
    source: str

    def __post_init__(self) -> None:
        base_currency = CurrencyCode(str(self.base_currency))
        quote_currency = CurrencyCode(str(self.quote_currency))
        if base_currency == quote_currency:
            raise ValueError("FX base and quote currencies must differ.")
        if self.rate <= 0:
            raise ValueError("FX rate must be positive.")
        if self.effective_at.tzinfo is None or self.effective_at.utcoffset() is None:
            raise ValueError("FX timestamps must be timezone-aware.")
        if not self.source.strip():
            raise ValueError("FX rate source is required.")
        object.__setattr__(self, "base_currency", base_currency)
        object.__setattr__(self, "quote_currency", quote_currency)
        object.__setattr__(self, "rate", _decimal_value(self.rate, "FX rate"))


class FxRateSource(Protocol):
    """Provider-neutral boundary for externally supplied FX-rate records."""

    def get_rate(
        self,
        base_currency: CurrencyCode,
        quote_currency: CurrencyCode,
        effective_at: datetime,
    ) -> FxRate:
        """Return a supplied FX rate; implementations may live outside the core."""


def is_rate_current(rate: FxRate, as_of: datetime, max_age: timedelta) -> bool:
    """Return whether a supplied rate is within the caller's freshness policy."""
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("FX policy timestamps must be timezone-aware.")
    if max_age < timedelta(0):
        raise ValueError("FX maximum age must be non-negative.")
    return as_of - rate.effective_at <= max_age


__all__ = [
    "AllocationRule",
    "AllocationRuleSchedule",
    "AssetCategory",
    "AssetDefinition",
    "FxRate",
    "FxRateSource",
    "InvestmentActivity",
    "InvestmentActivityRegistry",
    "InvestmentActivityType",
    "InvestmentValuation",
    "Liability",
    "LiabilityRegistry",
    "ManualValuation",
    "MemberUnitLedger",
    "ScheduledAllocationRule",
    "is_rate_current",
]
