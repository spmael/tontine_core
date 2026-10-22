"""Immutable records used by hybrid contribution allocation."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_DOWN, Decimal, localcontext
from enum import StrEnum

from tontine._datetime import require_aware_datetime
from tontine.currencies import CurrencyCode

from .rules import HybridRule


class PendingAllocationReason(StrEnum):
    """Reason a received contribution is awaiting a usable valuation."""

    NO_VALUATION = "no_valuation"
    STALE_VALUATION = "stale_valuation"


class AllocationType(StrEnum):
    """Recorded source that generated an investment allocation."""

    CONTRIBUTION = "contribution"
    CATCH_UP = "catch_up"


def _text(value: str, label: str) -> None:
    if not value.strip():
        raise ValueError(f"{label} is required.")


def _integer(value: int, label: str, minimum: int) -> None:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label} must be an integer of at least {minimum}.")


def _decimal(value: Decimal, label: str, *, positive: bool = False) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{label} must be a Decimal.")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite.")
    if value < 0 or (positive and value == 0):
        qualifier = "positive" if positive else "non-negative"
        raise ValueError(f"{label} must be {qualifier}.")
    return value


def _offset(value: Decimal, label: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{label} must be a Decimal.")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite.")
    if value > 0:
        raise ValueError(f"{label} must be zero or negative.")
    return value


def _working_precision(*values: Decimal) -> int:
    precision = 0
    for value in values:
        exponent = value.as_tuple().exponent
        if not isinstance(exponent, int):
            raise ValueError("Amounts must be finite.")
        precision += len(value.as_tuple().digits) + abs(exponent)
    return max(28, precision + 12)


@dataclass(frozen=True)
class HybridUnitValuation:
    """Record a manually supplied per-unit price and its effective date."""

    valuation_id: str
    effective_date: date
    unit_price: Decimal
    currency: CurrencyCode

    def __post_init__(self) -> None:
        _text(self.valuation_id, "Valuation identifier")
        object.__setattr__(
            self, "unit_price", _decimal(self.unit_price, "Unit price", positive=True)
        )
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))


@dataclass(frozen=True)
class PendingHybridAllocation:
    """Hold a recorded fund share until a current per-unit valuation is usable."""

    allocation_id: str
    contribution_id: str
    member_id: str
    cycle_id: str
    cycle_number: int
    rule_version: int
    payment_order_version: int
    received_amount: Decimal
    currency: CurrencyCode
    receipt_date: date
    pot_amount: Decimal
    fund_amount: Decimal
    reason: PendingAllocationReason
    allocation_type: AllocationType = AllocationType.CONTRIBUTION
    source_arrears_id: str | None = None

    def __post_init__(self) -> None:
        for identifier, label in (
            (self.allocation_id, "Allocation identifier"),
            (self.contribution_id, "Contribution identifier"),
            (self.member_id, "Member identifier"),
            (self.cycle_id, "Cycle identifier"),
        ):
            _text(identifier, label)
        for number, label in (
            (self.cycle_number, "Cycle number"),
            (self.rule_version, "Rule version"),
            (self.payment_order_version, "Payment-order version"),
        ):
            _integer(number, label, 1)
        object.__setattr__(
            self, "received_amount", _decimal(self.received_amount, "Received amount")
        )
        object.__setattr__(self, "pot_amount", _decimal(self.pot_amount, "Pot amount"))
        object.__setattr__(
            self, "fund_amount", _decimal(self.fund_amount, "Fund amount")
        )
        with localcontext() as context:
            context.prec = _working_precision(
                self.received_amount, self.pot_amount, self.fund_amount
            )
            if self.pot_amount + self.fund_amount != self.received_amount:
                raise ValueError("Pot and fund amounts must equal the received amount.")
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        object.__setattr__(self, "reason", PendingAllocationReason(self.reason))
        object.__setattr__(
            self, "allocation_type", AllocationType(self.allocation_type)
        )
        self._validate_source()

    def _validate_source(self) -> None:
        if self.allocation_type is AllocationType.CATCH_UP:
            if self.source_arrears_id is None:
                raise ValueError("Catch-up allocations require an arrears reference.")
            _text(self.source_arrears_id, "Arrears identifier")
        elif self.source_arrears_id is not None:
            raise ValueError("Contribution allocations cannot reference arrears.")


@dataclass(frozen=True)
class HybridAllocation:
    """Store the resolved split, price, unit quantity, and source references.

    ``valuation_reference`` and ``valuation_date`` are ``None`` when the
    configured launch price was used.
    """

    allocation_id: str
    contribution_id: str
    member_id: str
    cycle_id: str
    cycle_number: int
    rule_version: int
    payment_order_version: int
    received_amount: Decimal
    currency: CurrencyCode
    receipt_date: date
    allocated_on: date
    valuation_reference: str | None
    valuation_date: date | None
    unit_price: Decimal
    pot_amount: Decimal
    fund_amount: Decimal
    units_issued: Decimal
    cash_residual: Decimal
    allocation_type: AllocationType = AllocationType.CONTRIBUTION
    source_arrears_id: str | None = None

    def __post_init__(self) -> None:
        for identifier, label in (
            (self.allocation_id, "Allocation identifier"),
            (self.contribution_id, "Contribution identifier"),
            (self.member_id, "Member identifier"),
            (self.cycle_id, "Cycle identifier"),
        ):
            _text(identifier, label)
        for number, label in (
            (self.cycle_number, "Cycle number"),
            (self.rule_version, "Rule version"),
            (self.payment_order_version, "Payment-order version"),
        ):
            _integer(number, label, 1)
        if self.allocated_on < self.receipt_date:
            raise ValueError("Allocation date must not precede the receipt date.")
        if self.valuation_date is not None and self.valuation_date > self.allocated_on:
            raise ValueError("Valuation date must not follow the allocation date.")
        if (self.valuation_reference is None) != (self.valuation_date is None):
            raise ValueError(
                "Valuation reference and valuation date must both be present or absent."
            )
        if self.valuation_reference is not None:
            _text(self.valuation_reference, "Valuation reference")
        for name in ("received_amount", "pot_amount", "fund_amount", "cash_residual"):
            object.__setattr__(self, name, _decimal(getattr(self, name), name))
        price = _decimal(self.unit_price, "Unit price", positive=True)
        units = _decimal(self.units_issued, "Units issued")
        object.__setattr__(self, "unit_price", price)
        object.__setattr__(self, "units_issued", units)
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        object.__setattr__(
            self, "allocation_type", AllocationType(self.allocation_type)
        )
        self._validate_source()
        with localcontext() as context:
            context.prec = _working_precision(
                self.received_amount,
                self.pot_amount,
                self.fund_amount,
                self.unit_price,
                self.units_issued,
                self.cash_residual,
            )
            if self.pot_amount + self.fund_amount != self.received_amount:
                raise ValueError("Pot and fund amounts must equal the received amount.")
            if self.units_issued != self.units_issued.quantize(Decimal("0.0001")):
                raise ValueError("Issued units must be rounded to four decimal places.")
            if self.units_issued * self.unit_price + self.cash_residual != (
                self.fund_amount
            ):
                raise ValueError("Units and cash residual must equal the fund amount.")

    def _validate_source(self) -> None:
        if self.allocation_type is AllocationType.CATCH_UP:
            if self.source_arrears_id is None:
                raise ValueError("Catch-up allocations require an arrears reference.")
            _text(self.source_arrears_id, "Arrears identifier")
        elif self.source_arrears_id is not None:
            raise ValueError("Contribution allocations cannot reference arrears.")


@dataclass(frozen=True)
class AllocationReversal:
    """Record a linked offset of an allocation at its original price."""

    reversal_id: str
    original_allocation_id: str
    contribution_id: str
    member_id: str
    reason: str
    recorded_at: datetime
    currency: CurrencyCode
    unit_price: Decimal
    pot_offset: Decimal
    fund_offset: Decimal
    units_offset: Decimal
    cash_residual_offset: Decimal

    def __post_init__(self) -> None:
        for value, label in (
            (self.reversal_id, "Reversal identifier"),
            (self.original_allocation_id, "Original allocation identifier"),
            (self.contribution_id, "Contribution identifier"),
            (self.member_id, "Member identifier"),
            (self.reason, "Reversal reason"),
        ):
            _text(value, label)
        require_aware_datetime(self.recorded_at, "recorded_at")
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        object.__setattr__(
            self, "unit_price", _decimal(self.unit_price, "Unit price", positive=True)
        )
        for name in (
            "pot_offset",
            "fund_offset",
            "units_offset",
            "cash_residual_offset",
        ):
            object.__setattr__(self, name, _offset(getattr(self, name), name))


def _price_and_valuation(
    *,
    rule: HybridRule,
    valuations: Iterable[HybridUnitValuation],
    as_of: date,
    units_outstanding: Decimal,
) -> tuple[Decimal, str | None, date | None, PendingAllocationReason | None]:
    if units_outstanding == 0:
        return rule.launch_unit_price, None, None, None
    eligible = []
    for valuation in valuations:
        if valuation.currency != rule.currency:
            raise ValueError("Valuation currency must match the hybrid rule currency.")
        if valuation.effective_date <= as_of:
            eligible.append(valuation)
    if not eligible:
        return Decimal("0"), None, None, PendingAllocationReason.NO_VALUATION
    valuation = max(eligible, key=lambda item: (item.effective_date, item.valuation_id))
    age_days = (as_of - valuation.effective_date).days
    if age_days > rule.max_valuation_age_days:
        return Decimal("0"), None, None, PendingAllocationReason.STALE_VALUATION
    return (
        valuation.unit_price,
        valuation.valuation_id,
        valuation.effective_date,
        None,
    )


def _units_and_residual(
    fund_amount: Decimal, unit_price: Decimal
) -> tuple[Decimal, Decimal]:
    with localcontext() as context:
        context.prec = _working_precision(fund_amount, unit_price)
        units = (fund_amount / unit_price).quantize(
            Decimal("0.0001"), rounding=ROUND_DOWN
        )
        residual = fund_amount - units * unit_price
    return units, residual
