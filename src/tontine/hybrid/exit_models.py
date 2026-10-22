"""Immutable records used by hybrid member exit processing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from enum import StrEnum
from typing import Protocol

from tontine._datetime import require_aware_datetime
from tontine.currencies import CurrencyCode, smallest_unit
from tontine.governance import MemberExitEffect, MemberExitType, PayoutDeferralEffect


class ExitStatus(StrEnum):
    """Current state of an exit settlement or payout entitlement."""

    PENDING_VALUATION = "pending_valuation"
    QUEUED = "queued"
    PAYABLE = "payable"
    HELD_FOR_ESTATE = "held_for_estate"
    CONSIGNED = "consigned"
    PAID_EXTERNALLY = "paid_externally"
    AMOUNT_OWED = "amount_owed"
    NO_PAYOUT = "no_payout"


class ExitGovernanceLookup(Protocol):
    """Approved exit and deferral decisions required by exit processing."""

    def approved_member_exit(self, proposal_id: str) -> MemberExitEffect: ...

    def approved_payout_deferral(self, proposal_id: str) -> PayoutDeferralEffect: ...


@dataclass(frozen=True)
class ExitSettlement:
    """Ordered exit calculation in group currency, rounded half-even to minor units."""

    valuation_id: str
    valuation_date: date
    units_redeemed: Decimal
    gross_unit_value: Decimal
    exit_fee: Decimal
    unpaid_penalties: Decimal
    unpaid_rotation_dues: Decimal
    unpaid_fund_dues: Decimal
    excess_pot_received: Decimal
    net_amount: Decimal
    currency: CurrencyCode

    def __post_init__(self) -> None:
        _identifier(self.valuation_id, "Valuation identifier")
        if type(self.valuation_date) is not date:
            raise TypeError("Valuation date must be a calendar date.")
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        for name in (
            "units_redeemed",
            "gross_unit_value",
            "exit_fee",
            "unpaid_penalties",
            "unpaid_rotation_dues",
            "unpaid_fund_dues",
            "excess_pot_received",
            "net_amount",
        ):
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                raise TypeError(f"{name} must be a Decimal.")
            if not value.is_finite():
                raise ValueError(f"{name} must be finite.")
            if name != "net_amount" and value < 0:
                raise ValueError(f"{name} must be non-negative.")
            if (
                name != "units_redeemed"
                and _currency_amount(value, self.currency) != value
            ):
                raise ValueError(f"{name} exceeds currency minor-unit precision.")
        if self.units_redeemed != self.units_redeemed.quantize(Decimal("0.0001")):
            raise ValueError("Redeemed units must use four decimal places.")
        expected_net = _net_amount(
            self.gross_unit_value,
            self.exit_fee,
            self.unpaid_penalties,
            self.unpaid_rotation_dues,
            self.unpaid_fund_dues,
            self.excess_pot_received,
        )
        if expected_net != self.net_amount:
            raise ValueError("Settlement net must equal its ordered monetary lines.")

    @property
    def lines(self) -> tuple[tuple[str, Decimal], ...]:
        """Return the monetary calculation in its prescribed display order."""
        return (
            ("gross_unit_value", self.gross_unit_value),
            ("exit_fee", -self.exit_fee),
            ("unpaid_penalties", -self.unpaid_penalties),
            ("unpaid_rotation_dues", -self.unpaid_rotation_dues),
            ("unpaid_fund_dues", -self.unpaid_fund_dues),
            ("excess_pot_received", -self.excess_pot_received),
            ("net_amount", self.net_amount),
        )

    @property
    def exit_fee_destination(self) -> str:
        """Return the required destination for the exit fee."""
        return "fund"


@dataclass(frozen=True)
class HybridExit:
    """Immutable current view of an approved exit and its status transitions."""

    exit_id: str
    proposal_id: str
    member_id: str
    exit_type: MemberExitType
    exit_date: date
    request_cycle: int
    rule_version: int
    currency: CurrencyCode
    fee_percent: Decimal
    payout_due_date: date
    requested_at: datetime
    status: ExitStatus
    settlement: ExitSettlement | None = None
    estate_proof_reference: str | None = None
    consignment_reference: str | None = None
    external_payment_reference: str | None = None
    queue_position: int | None = None

    def __post_init__(self) -> None:
        for value, label in (
            (self.exit_id, "Exit identifier"),
            (self.proposal_id, "Governance decision identifier"),
            (self.member_id, "Member identifier"),
        ):
            _identifier(value, label)
        if type(self.exit_date) is not date or type(self.payout_due_date) is not date:
            raise TypeError("Exit and payout dates must be calendar dates.")
        if type(self.request_cycle) is not int or self.request_cycle < 1:
            raise ValueError("Exit request cycle must be positive.")
        if type(self.rule_version) is not int or self.rule_version < 1:
            raise ValueError("Exit rule version must be positive.")
        if (
            not isinstance(self.fee_percent, Decimal)
            or not self.fee_percent.is_finite()
        ):
            raise ValueError("Exit fee must be a finite Decimal percentage.")
        if not Decimal("0") <= self.fee_percent < Decimal("100"):
            raise ValueError("Exit fee must be at least zero and below 100 percent.")
        object.__setattr__(self, "exit_type", MemberExitType(self.exit_type))
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        object.__setattr__(self, "status", ExitStatus(self.status))
        require_aware_datetime(self.requested_at, "requested_at")
        if self.settlement is not None and self.settlement.currency != self.currency:
            raise ValueError("Exit settlement currency must match the exit currency.")
        if self.queue_position is not None and self.queue_position < 1:
            raise ValueError("Queue position must be positive.")


@dataclass(frozen=True)
class ExitQueueEntry:
    """Position and amount assigned by a liquidity-limited payout report."""

    exit_id: str
    member_id: str
    position: int
    amount: Decimal
    status: ExitStatus

    def __post_init__(self) -> None:
        _identifier(self.exit_id, "Exit identifier")
        _identifier(self.member_id, "Member identifier")
        if type(self.position) is not int or self.position < 1:
            raise ValueError("Queue position must be positive.")
        if not isinstance(self.amount, Decimal) or not self.amount.is_finite():
            raise ValueError("Queue amount must be a finite Decimal.")
        if self.amount <= 0:
            raise ValueError("Queued entitlement must be positive.")
        object.__setattr__(self, "status", ExitStatus(self.status))
        if self.status not in {ExitStatus.QUEUED, ExitStatus.PAYABLE}:
            raise ValueError("Queue entries must be queued or payable.")


@dataclass(frozen=True)
class ExitQueueReport:
    """FIFO payout queue calculated against an explicitly supplied liquidity cap."""

    report_id: str
    currency: CurrencyCode
    liquidity_cap: Decimal
    entries: tuple[ExitQueueEntry, ...]
    created_at: datetime

    def __post_init__(self) -> None:
        _identifier(self.report_id, "Queue report identifier")
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        if (
            not isinstance(self.liquidity_cap, Decimal)
            or not self.liquidity_cap.is_finite()
        ):
            raise ValueError("Liquidity cap must be a finite Decimal.")
        if self.liquidity_cap < 0:
            raise ValueError("Liquidity cap must be non-negative.")
        object.__setattr__(self, "entries", tuple(self.entries))
        if len({item.exit_id for item in self.entries}) != len(self.entries):
            raise ValueError("Queue report cannot repeat an exit.")
        require_aware_datetime(self.created_at, "created_at")


def _currency_amount(value: Decimal, currency: CurrencyCode) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError("Settlement amounts must be Decimal values.")
    if not value.is_finite():
        raise ValueError("Settlement amounts must be finite.")
    unit = smallest_unit(currency)
    if unit is None:
        raise ValueError("Settlement currency must have a minor unit.")
    exponent = value.as_tuple().exponent
    if not isinstance(exponent, int):
        raise ValueError("Settlement amounts must be finite.")
    with localcontext() as context:
        context.prec = max(28, len(value.as_tuple().digits) + abs(exponent) + 8)
        return value.quantize(unit, rounding=ROUND_HALF_EVEN)


def _net_amount(gross: Decimal, *deductions: Decimal) -> Decimal:
    return _sum_amounts(gross, *(-value for value in deductions))


def _sum_amounts(*values: Decimal) -> Decimal:
    precision = 0
    for value in values:
        exponent = value.as_tuple().exponent
        if not isinstance(exponent, int):
            raise ValueError("Settlement amounts must be finite.")
        precision += len(value.as_tuple().digits) + abs(exponent)
    with localcontext() as context:
        context.prec = max(28, precision + 12)
        return sum(values, Decimal("0"))


def _multiply(left: Decimal, right: Decimal) -> Decimal:
    left_exponent = left.as_tuple().exponent
    right_exponent = right.as_tuple().exponent
    if not isinstance(left_exponent, int) or not isinstance(right_exponent, int):
        raise ValueError("Settlement inputs must be finite.")
    precision = (
        len(left.as_tuple().digits)
        + len(right.as_tuple().digits)
        + abs(left_exponent)
        + abs(right_exponent)
        + 12
    )
    with localcontext() as context:
        context.prec = max(28, precision)
        return left * right


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    last_day = (date(year + (month == 12), month % 12 + 1, 1) - date.resolution).day
    return date(year, month, min(value.day, last_day))


def _identifier(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required.")


__all__ = [
    "ExitQueueEntry",
    "ExitQueueReport",
    "ExitGovernanceLookup",
    "ExitSettlement",
    "ExitStatus",
    "HybridExit",
]
