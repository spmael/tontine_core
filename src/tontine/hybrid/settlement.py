"""Pure member settlement projections from recorded hybrid events."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, localcontext

from tontine.classic import ClassicPayout
from tontine.contributions import CycleStatus
from tontine.currencies import CurrencyCode
from tontine.members import Member

from .allocation_models import (
    AllocationReversal,
    HybridAllocation,
    HybridUnitValuation,
    PendingHybridAllocation,
)
from .arrears import (
    CatchUpElection,
    ExitArrearsOffset,
    PaymentApplication,
    RotationArrearsOffset,
)
from .exit_models import ExitStatus, HybridExit
from .rules import StatuteFlags
from .settlement_history import HybridSettlementHistory

_CurrencyRecord = (
    HybridAllocation
    | PendingHybridAllocation
    | AllocationReversal
    | PaymentApplication
    | ClassicPayout
    | RotationArrearsOffset
    | ExitArrearsOffset
    | HybridExit
)
_PENDING_EXIT_STATUSES = frozenset(
    {
        ExitStatus.AMOUNT_OWED,
        ExitStatus.PENDING_VALUATION,
        ExitStatus.QUEUED,
        ExitStatus.PAYABLE,
        ExitStatus.HELD_FOR_ESTATE,
        ExitStatus.CONSIGNED,
    }
)


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


def _require_currencies(
    records: Iterable[_CurrencyRecord],
    currency: CurrencyCode,
    label: str,
) -> None:
    if any(item.currency != currency for item in records):
        raise ValueError(f"{label} currency must match the hybrid rule.")


@dataclass(frozen=True)
class HybridSettlementPosition:
    """Member dues, rotation-pot history, and unit valuation."""

    member_id: str
    currency: CurrencyCode
    rotation_paid_in: Decimal
    rotation_received: Decimal
    rotation_position: Decimal
    open_contribution_dues: Decimal
    unpaid_rotation_dues: Decimal
    unpaid_fund_dues: Decimal
    unpaid_penalties: Decimal
    units: Decimal
    unit_price: Decimal | None
    unit_value: Decimal | None
    statute_flags: StatuteFlags
    pending_allocations: tuple[PendingHybridAllocation, ...]
    pending_exits: tuple[HybridExit, ...]
    elections: tuple[CatchUpElection, ...]
    rotation_offsets: tuple[RotationArrearsOffset, ...]
    exit_offsets: tuple[ExitArrearsOffset, ...]

    def __post_init__(self) -> None:
        if not self.member_id.strip():
            raise ValueError("Settlement member identifier is required.")
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        for name in (
            "rotation_paid_in",
            "rotation_received",
            "open_contribution_dues",
            "unpaid_rotation_dues",
            "unpaid_fund_dues",
            "unpaid_penalties",
            "units",
        ):
            value = getattr(self, name)
            if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
                raise ValueError(f"{name} must be a finite non-negative Decimal.")
        if not isinstance(self.rotation_position, Decimal) or not (
            self.rotation_position.is_finite()
        ):
            raise ValueError("Rotation position must be a finite Decimal.")
        if (self.unit_price is None) != (self.unit_value is None):
            raise ValueError("Unit price and value must be present together.")
        if self.unit_price is not None:
            if (
                not isinstance(self.unit_price, Decimal)
                or not self.unit_price.is_finite()
                or self.unit_price <= 0
            ):
                raise ValueError("Unit price must be a positive finite Decimal.")
        if self.unit_value is not None:
            if (
                not isinstance(self.unit_value, Decimal)
                or not self.unit_value.is_finite()
                or self.unit_value < 0
            ):
                raise ValueError("Unit value must be a non-negative finite Decimal.")
        if not isinstance(self.statute_flags, StatuteFlags):
            raise TypeError("Settlement position requires recorded statute flags.")
        for name in (
            "pending_allocations",
            "pending_exits",
            "elections",
            "rotation_offsets",
            "exit_offsets",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))

    @property
    def outstanding_dues(self) -> Decimal:
        """Return current-cycle dues and arrears in the group currency."""
        return _sum_amounts(
            self.open_contribution_dues,
            self.unpaid_rotation_dues,
            self.unpaid_fund_dues,
        )

    @property
    def total_owed(self) -> Decimal:
        """Return contribution dues plus unpaid penalties in the group currency."""
        return _sum_amounts(self.outstanding_dues, self.unpaid_penalties)


def settlement_position(
    history: HybridSettlementHistory,
    member: Member,
    valuation: HybridUnitValuation | None,
) -> HybridSettlementPosition:
    """Calculate a member's settlement position from recorded events only.

    Rotation position is pot contributions paid in less classic payouts received.
    Due, non-closed cycle expectations are combined with closed-cycle hybrid
    arrears. The supplied valuation is the recorded per-unit price used for the
    member-funds line.

    Args:
        history: Snapshot of the group's hybrid and classic settlement events.
        member: Member whose history is being projected.
        valuation: Recorded unit valuation, or ``None`` if no price is available.

    Returns:
        The immutable settlement position, with the pot line ranked before units.

    Raises:
        TypeError: If history, member, or valuation has the wrong type.
        ValueError: If the event currencies disagree or recorded balances are
            internally inconsistent.
    """
    if not isinstance(history, HybridSettlementHistory):
        raise TypeError("Expected a HybridSettlementHistory.")
    if not isinstance(member, Member):
        raise TypeError("Expected a Member.")
    if valuation is not None and not isinstance(valuation, HybridUnitValuation):
        raise TypeError("Expected a HybridUnitValuation or None.")

    rule = history.rule_schedule.versions[-1].rule
    currency = CurrencyCode(str(rule.currency))
    if valuation is not None and valuation.currency != currency:
        raise ValueError("Unit valuation currency must match the hybrid rule.")

    member_allocations = tuple(
        item for item in history.allocations if item.member_id == member.member_id
    )
    member_pending = tuple(
        item
        for item in history.pending_allocations
        if item.member_id == member.member_id
    )
    member_payments = tuple(
        item for item in history.payments if item.member_id == member.member_id
    )
    member_reversals = tuple(
        item for item in history.reversals if item.member_id == member.member_id
    )
    member_payouts = tuple(
        item for item in history.payouts if item.recipient_id == member.member_id
    )
    member_arrears = tuple(
        item for item in history.arrears_records if item.member_id == member.member_id
    )
    _require_currencies(member_allocations, currency, "Settlement event")
    _require_currencies(member_pending, currency, "Settlement event")
    _require_currencies(member_reversals, currency, "Settlement event")
    _require_currencies(member_payments, currency, "Settlement event")
    _require_currencies(member_payouts, currency, "Settlement event")

    rotation_paid_in = _sum_amounts(
        *(item.pot_amount for item in member_allocations),
        *(item.pot_amount for item in member_pending),
        *(item.rotation_paid for item in member_payments),
        *(item.pot_offset for item in member_reversals),
    )
    if rotation_paid_in < 0:
        raise ValueError("Allocation reversals exceed the member's pot contributions.")
    rotation_received = _sum_amounts(*(item.amount for item in member_payouts))
    rotation_position = _sum_amounts(rotation_paid_in, -rotation_received)

    unpaid_rotation: list[Decimal] = []
    unpaid_fund: list[Decimal] = []
    unpaid_penalties: list[Decimal] = []
    for record in member_arrears:
        if record.currency != currency:
            raise ValueError("Arrears currency must match the hybrid rule.")
        payments = tuple(
            item for item in member_payments if item.arrears_id == record.arrears_id
        )
        rotation_offsets = tuple(
            item
            for item in history.rotation_offsets
            if item.arrears_id == record.arrears_id
        )
        exit_offsets = tuple(
            item
            for item in history.exit_offsets
            if item.arrears_id == record.arrears_id
        )
        forfeitures = tuple(
            item for item in history.forfeitures if item.arrears_id == record.arrears_id
        )
        waivers = tuple(
            item for item in history.waivers if item.arrears_id == record.arrears_id
        )
        unpaid_rotation.append(
            max(
                _sum_amounts(
                    record.rotation_amount,
                    *(-item.rotation_paid for item in payments),
                    *(-item.amount for item in rotation_offsets),
                    *(-item.rotation_amount for item in exit_offsets),
                ),
                Decimal("0"),
            )
        )
        unpaid_fund.append(
            max(
                _sum_amounts(
                    record.fund_amount,
                    *(-item.fund_paid for item in payments),
                    *(-item.amount for item in forfeitures),
                    *(-item.fund_amount for item in exit_offsets),
                ),
                Decimal("0"),
            )
        )
        unpaid_penalties.append(
            max(
                _sum_amounts(
                    record.penalty_amount,
                    *(-item.penalty_paid for item in payments),
                    *(-item.amount for item in waivers),
                    *(-item.penalty_amount for item in exit_offsets),
                ),
                Decimal("0"),
            )
        )

    arrears_cycles = {(item.cycle_id, item.member_id) for item in member_arrears}
    open_dues: list[Decimal] = []
    open_penalties: list[Decimal] = []
    for cycle in history._contribution_cycles:
        if (
            cycle.status is not CycleStatus.DUE
            or (
                cycle.cycle_id,
                str(member.member_id),
            )
            in arrears_cycles
        ):
            continue
        contribution = next(
            (
                item
                for item in cycle.contributions
                if item.member_id == str(member.member_id)
            ),
            None,
        )
        if contribution is None:
            continue
        received = (
            Decimal("0")
            if contribution.actual_amount is None
            else contribution.actual_amount
        )
        open_dues.append(
            max(_sum_amounts(contribution.expected_amount, -received), Decimal("0"))
        )
        if contribution.penalty > 0:
            if cycle.penalty_currency != currency:
                raise ValueError("Open-cycle penalty currency must match the rule.")
            open_penalties.append(contribution.penalty)

    member_rotation_offsets = tuple(
        item for item in history.rotation_offsets if item.member_id == member.member_id
    )
    member_exit_offsets = tuple(
        item for item in history.exit_offsets if item.member_id == member.member_id
    )
    member_exits = tuple(
        item for item in history.exits if item.member_id == member.member_id
    )
    member_pending_exits = tuple(
        item for item in member_exits if item.status in _PENDING_EXIT_STATUSES
    )
    _require_currencies(member_rotation_offsets, currency, "Arrears offset")
    _require_currencies(member_exit_offsets, currency, "Arrears offset")
    _require_currencies(member_exits, currency, "Exit")

    redeemed_units = _sum_amounts(
        *(item.units for item in member_rotation_offsets),
        *(
            item.settlement.units_redeemed
            for item in member_exits
            if item.settlement is not None
        ),
    )
    unit_balance = _sum_amounts(
        *(item.units_issued for item in member_allocations),
        *(item.units_offset for item in member_reversals),
        -redeemed_units,
    )
    if unit_balance < 0:
        raise ValueError("Recorded redemptions exceed the member's issued units.")

    unit_value = (
        None if valuation is None else _multiply(unit_balance, valuation.unit_price)
    )
    statute_flags = rule.statute_flags
    return HybridSettlementPosition(
        member_id=str(member.member_id),
        currency=currency,
        rotation_paid_in=rotation_paid_in,
        rotation_received=rotation_received,
        rotation_position=rotation_position,
        open_contribution_dues=_sum_amounts(*open_dues),
        unpaid_rotation_dues=_sum_amounts(*unpaid_rotation),
        unpaid_fund_dues=_sum_amounts(*unpaid_fund),
        unpaid_penalties=_sum_amounts(*unpaid_penalties, *open_penalties),
        units=unit_balance,
        unit_price=None if valuation is None else valuation.unit_price,
        unit_value=unit_value,
        statute_flags=statute_flags,
        pending_allocations=member_pending,
        pending_exits=member_pending_exits,
        elections=tuple(
            item for item in history.elections if item.member_id == member.member_id
        ),
        rotation_offsets=member_rotation_offsets,
        exit_offsets=member_exit_offsets,
    )


__all__ = [
    "HybridSettlementHistory",
    "HybridSettlementPosition",
    "settlement_position",
]
