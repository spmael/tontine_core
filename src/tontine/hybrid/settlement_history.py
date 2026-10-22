"""Immutable snapshots of the events used for hybrid settlement reports."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import InitVar, dataclass, field
from decimal import Decimal

from tontine.classic import ClassicPayout
from tontine.contributions import ContributionCycle, CycleStatus
from tontine.currencies import CurrencyCode

from .allocation_models import (
    AllocationReversal,
    HybridAllocation,
    PendingHybridAllocation,
)
from .allocation_registry import HybridAllocationRegistry
from .arrears import (
    ArrearsRecord,
    CatchUpElection,
    ExitArrearsOffset,
    FundShareForfeiture,
    HybridArrearsRegistry,
    PaymentApplication,
    PenaltyWaiver,
    RotationArrearsOffset,
)
from .exit import HybridExitRegistry
from .exit_models import HybridExit
from .rules import HybridRuleSchedule


def _unique(values: Iterable[str | int], label: str) -> None:
    items = tuple(values)
    if len(set(items)) != len(items):
        raise ValueError(f"Settlement history contains duplicate {label}.")


@dataclass(frozen=True)
class _MemberContribution:
    member_id: str
    expected_amount: Decimal
    actual_amount: Decimal | None
    penalty: Decimal


@dataclass(frozen=True)
class _ContributionCycle:
    cycle_id: str
    status: CycleStatus
    penalty_currency: CurrencyCode | None
    contributions: tuple[_MemberContribution, ...]

    @classmethod
    def snapshot(cls, cycle: ContributionCycle) -> _ContributionCycle:
        def snapshot_contribution(
            member_id: str, expected_amount: Decimal
        ) -> _MemberContribution:
            contribution = cycle.recorded_contributions.get(member_id)
            return _MemberContribution(
                member_id=member_id,
                expected_amount=expected_amount,
                actual_amount=(
                    None if contribution is None else contribution.actual_amount
                ),
                penalty=(
                    Decimal("0") if contribution is None else contribution.penalty
                ),
            )

        return cls(
            cycle_id=cycle.cycle_id,
            status=cycle.status,
            penalty_currency=cycle.penalty_currency,
            contributions=tuple(
                snapshot_contribution(member_id, expected_amount)
                for member_id, expected_amount in cycle.expected_contributions.items()
            ),
        )


@dataclass(frozen=True)
class HybridSettlementHistory:
    """Immutable snapshot of hybrid events used to calculate a member position."""

    rule_schedule: HybridRuleSchedule
    contribution_cycles: InitVar[Iterable[ContributionCycle]] = ()
    payouts: tuple[ClassicPayout, ...] = ()
    allocations: tuple[HybridAllocation, ...] = ()
    pending_allocations: tuple[PendingHybridAllocation, ...] = ()
    reversals: tuple[AllocationReversal, ...] = ()
    arrears_records: tuple[ArrearsRecord, ...] = ()
    payments: tuple[PaymentApplication, ...] = ()
    elections: tuple[CatchUpElection, ...] = ()
    forfeitures: tuple[FundShareForfeiture, ...] = ()
    waivers: tuple[PenaltyWaiver, ...] = ()
    rotation_offsets: tuple[RotationArrearsOffset, ...] = ()
    exit_offsets: tuple[ExitArrearsOffset, ...] = ()
    exits: tuple[HybridExit, ...] = ()
    _contribution_cycles: tuple[_ContributionCycle, ...] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self, contribution_cycles: Iterable[ContributionCycle]) -> None:
        object.__setattr__(
            self,
            "_contribution_cycles",
            tuple(_ContributionCycle.snapshot(cycle) for cycle in contribution_cycles),
        )
        for name in (
            "payouts",
            "allocations",
            "pending_allocations",
            "reversals",
            "arrears_records",
            "payments",
            "elections",
            "forfeitures",
            "waivers",
            "rotation_offsets",
            "exit_offsets",
            "exits",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        if not isinstance(self.rule_schedule, HybridRuleSchedule):
            raise TypeError("Settlement history requires a HybridRuleSchedule.")
        _unique(
            (item.cycle_id for item in self._contribution_cycles),
            "contribution cycle",
        )
        _unique((item.cycle_number for item in self.payouts), "payout cycle")
        _unique((item.allocation_id for item in self.allocations), "allocation")
        _unique(
            (item.contribution_id for item in self.allocations),
            "allocation contribution",
        )
        _unique(
            (item.allocation_id for item in self.pending_allocations),
            "pending allocation",
        )
        _unique((item.reversal_id for item in self.reversals), "reversal")
        _unique((item.arrears_id for item in self.arrears_records), "arrears record")
        _unique((item.payment_id for item in self.payments), "payment")
        _unique((item.election_id for item in self.elections), "election")
        _unique((item.forfeiture_id for item in self.forfeitures), "forfeiture")
        _unique((item.waiver_id for item in self.waivers), "penalty waiver")
        _unique((item.offset_id for item in self.rotation_offsets), "rotation offset")
        _unique((item.offset_id for item in self.exit_offsets), "exit offset")
        _unique((item.exit_id for item in self.exits), "exit")

    @classmethod
    def from_registries(
        cls,
        *,
        rule_schedule: HybridRuleSchedule,
        allocation_registry: HybridAllocationRegistry,
        arrears_registry: HybridArrearsRegistry,
        exit_registry: HybridExitRegistry,
        contribution_cycles: Iterable[ContributionCycle],
        payouts: Iterable[ClassicPayout],
    ) -> HybridSettlementHistory:
        """Snapshot the records held by the hybrid registries.

        Args:
            rule_schedule: Recorded group rules, including statute facts.
            allocation_registry: Resolved and pending contribution allocations.
            arrears_registry: Arrears, payments, elections, waivers, and offsets.
            exit_registry: Recorded member exits.
            contribution_cycles: Recorded cycles, including currently due items.
            payouts: Classic payout records from the same group history.

        Returns:
            An immutable event snapshot suitable for repeated pure calculations.
        """
        return cls(
            rule_schedule=rule_schedule,
            contribution_cycles=tuple(contribution_cycles),
            payouts=tuple(payouts),
            allocations=allocation_registry.allocations(),
            pending_allocations=allocation_registry.pending_allocations(),
            reversals=allocation_registry.reversals(),
            arrears_records=arrears_registry.records(),
            payments=arrears_registry.payments(),
            elections=arrears_registry.elections(),
            forfeitures=arrears_registry.forfeitures(),
            waivers=arrears_registry.waivers(),
            rotation_offsets=arrears_registry.offsets(),
            exit_offsets=arrears_registry.exit_offsets(),
            exits=exit_registry.exits(),
        )


__all__ = ["HybridSettlementHistory"]
