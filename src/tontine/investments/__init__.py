"""Investment allocation, valuation, and supplied FX-rate vocabulary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Protocol

from tontine.currencies import CurrencyCode


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
        """Record supplied investment activity without executing a transaction."""
        from tontine.exceptions import DuplicateInvestmentEventError

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
        """Return the attributable value for supplied member units."""
        return _non_negative(units, "Member units") * self.unit_price


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
        """Issue units from a contribution amount and explicit unit price."""
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
        """Redeem units without mutating prior unit events."""
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
    "AssetCategory",
    "AssetDefinition",
    "FxRate",
    "FxRateSource",
    "InvestmentActivity",
    "InvestmentActivityRegistry",
    "InvestmentActivityType",
    "InvestmentValuation",
    "ManualValuation",
    "MemberUnitLedger",
    "is_rate_current",
]
