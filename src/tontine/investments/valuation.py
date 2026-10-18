"""Liabilities, NAV valuation, and member unit balances."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from tontine.currencies import CurrencyCode

from ._values import _non_negative


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
    """Derive NAV and member values from supplied Decimal valuation inputs.

    Zero units outstanding is the valid state before the first unit issue
    (ADR-005). NAV is still defined, but per-unit values are ``None`` because
    no unit price can be derived.
    """

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

    @property
    def has_units_outstanding(self) -> bool:
        """Return whether any units are outstanding."""
        return self.units_outstanding > 0

    @property
    def nav(self) -> Decimal:
        """Return net asset value as assets less liabilities."""
        return self.assets - self.liabilities

    @property
    def unit_price(self) -> Decimal | None:
        """Return unquantized NAV per unit, or ``None`` with no units outstanding."""
        if not self.has_units_outstanding:
            return None
        return self.nav / self.units_outstanding

    def member_value(self, units: Decimal | int | str) -> Decimal | None:
        """Return the attributable value for supplied member units.

        Args:
            units: Non-negative member units in the valuation's unit system.

        Returns:
            Units multiplied by the unquantized Decimal unit price, or ``None``
            when no units are outstanding.
        """
        normalized_units = _non_negative(units, "Member units")
        unit_price = self.unit_price
        if unit_price is None:
            return None
        return normalized_units * unit_price

    def member_ownership_percentage(self, units: Decimal | int | str) -> Decimal | None:
        """Return a member's percentage of total outstanding units.

        Returns:
            The unquantized percentage, or ``None`` when no units are
            outstanding.

        Raises:
            ValueError: If units are negative or exceed total outstanding units.
        """
        normalized_units = _non_negative(units, "Member units")
        if normalized_units > self.units_outstanding:
            raise ValueError("Member units cannot exceed total outstanding units.")
        if not self.has_units_outstanding:
            return None
        return normalized_units / self.units_outstanding * Decimal("100")

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
        """Create a valuation using liabilities aggregated from a registry.

        Args:
            assets: Non-negative asset total in the supplied asset currency.
            liabilities: Registry of manually supplied liabilities.
            currency: ISO 4217 liability currency to aggregate from the registry.
            units_outstanding: Non-negative outstanding unit total for the valuation.
            asset_currency: ISO 4217 asset currency, which must match ``currency``.

        Raises:
            ValueError: If the asset and liability currencies do not match.
        """
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
