"""Append-only records for hybrid contribution arrears and catch-up choices."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from enum import StrEnum
from typing import Protocol
from zoneinfo import ZoneInfo

from tontine._datetime import require_aware_datetime
from tontine.audit import AuditEvent, AuditEventRegistry
from tontine.contributions import (
    ContributionCycle,
    ContributionStatus,
    CycleStatus,
)
from tontine.currencies import CurrencyCode, smallest_unit
from tontine.exceptions import MissingRecordError
from tontine.governance import PenaltyWaiverEffect
from tontine.investments import MemberUnitLedger, UnitRedemptionEvent

from .allocation import (
    AllocationType,
    HybridAllocation,
    HybridAllocationRegistry,
    HybridUnitValuation,
    PendingHybridAllocation,
)
from .arrears_snapshots import HybridArrearsSnapshot
from .rules import (
    CatchUpOutcome,
    ContributionPaymentOrder,
    HybridRuleVersion,
    PenaltyPaymentOrder,
)
from .split import split_contribution


class CatchUpChoice(StrEnum):
    """Member choice for an unpaid investment share."""

    CATCH_UP = "catch_up"
    FORFEIT = "forfeit"


class ForfeitureCause(StrEnum):
    """Reason an unpaid investment share stopped being recoverable."""

    MEMBER_ELECTED = "member_elected"
    DEFAULTED = "defaulted"
    CATCH_UP_EXPIRED = "catch_up_expired"
    CATCH_UP_DISABLED = "catch_up_disabled"


class PenaltyWaiverLookup(Protocol):
    """Governance lookup required to confirm an approved penalty waiver."""

    def approved_penalty_waiver(self, proposal_id: str) -> PenaltyWaiverEffect: ...


@dataclass(frozen=True)
class ArrearsRecord:
    """Capture a cycle's unpaid rotation, investment, and penalty amounts."""

    arrears_id: str
    member_id: str
    cycle_id: str
    cycle_number: int
    rule_version: int
    currency: CurrencyCode
    rotation_amount: Decimal
    fund_amount: Decimal
    penalty_amount: Decimal
    penalty_assessment_id: str | None
    penalty_destination: str | None
    catch_up_allowed: bool
    catch_up_deadline_cycle: int
    default_outcome: CatchUpOutcome
    closed_at: datetime

    def __post_init__(self) -> None:
        for value, label in (
            (self.arrears_id, "Arrears identifier"),
            (self.member_id, "Member identifier"),
            (self.cycle_id, "Cycle identifier"),
        ):
            _text(value, label)
        _positive_integer(self.cycle_number, "Cycle number")
        _positive_integer(self.rule_version, "Rule version")
        _positive_integer(self.catch_up_deadline_cycle, "Catch-up deadline cycle")
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        for name in ("rotation_amount", "fund_amount", "penalty_amount"):
            object.__setattr__(self, name, _money(getattr(self, name), name))
        if self.penalty_amount > 0:
            if not self.penalty_assessment_id or not self.penalty_destination:
                raise ValueError(
                    "Assessed penalties require their source and destination."
                )
        elif (
            self.penalty_assessment_id is not None
            or self.penalty_destination is not None
        ):
            raise ValueError("Penalty provenance is only valid for a positive penalty.")
        if type(self.catch_up_allowed) is not bool:
            raise TypeError("Catch-up allowed must be a boolean.")
        object.__setattr__(
            self, "default_outcome", CatchUpOutcome(self.default_outcome)
        )
        require_aware_datetime(self.closed_at, "closed_at")


@dataclass(frozen=True)
class ArrearsBalance:
    """Return the unpaid amounts derived from recorded arrears events."""

    rotation_amount: Decimal
    fund_amount: Decimal
    penalty_amount: Decimal


@dataclass(frozen=True)
class CatchUpElection:
    """Record a member choice or deadline default for one arrears record."""

    election_id: str
    arrears_id: str
    member_id: str
    choice: CatchUpChoice
    cycle_number: int
    elected_at: datetime
    is_default: bool = False

    def __post_init__(self) -> None:
        for value, label in (
            (self.election_id, "Election identifier"),
            (self.arrears_id, "Arrears identifier"),
            (self.member_id, "Member identifier"),
        ):
            _text(value, label)
        _positive_integer(self.cycle_number, "Election cycle number")
        object.__setattr__(self, "choice", CatchUpChoice(self.choice))
        if type(self.is_default) is not bool:
            raise TypeError("Default election flag must be a boolean.")
        if self.is_default and self.choice is not CatchUpChoice.FORFEIT:
            raise ValueError("A deadline default can only forfeit the fund share.")
        require_aware_datetime(self.elected_at, "elected_at")


@dataclass(frozen=True)
class FundShareForfeiture:
    """Record the amount of one missed fund share that is no longer recoverable."""

    forfeiture_id: str
    arrears_id: str
    member_id: str
    amount: Decimal
    cause: ForfeitureCause
    occurred_at: datetime

    def __post_init__(self) -> None:
        for value, label in (
            (self.forfeiture_id, "Forfeiture identifier"),
            (self.arrears_id, "Arrears identifier"),
            (self.member_id, "Member identifier"),
        ):
            _text(value, label)
        object.__setattr__(self, "amount", _money(self.amount, "Forfeited amount"))
        if self.amount == 0:
            raise ValueError("Forfeited amount must be positive.")
        object.__setattr__(self, "cause", ForfeitureCause(self.cause))
        require_aware_datetime(self.occurred_at, "occurred_at")


@dataclass(frozen=True)
class PaymentApplication:
    """Record how an already received amount was applied to arrears."""

    payment_id: str
    arrears_id: str
    member_id: str
    cycle_id: str
    cycle_number: int
    rule_version: int
    currency: CurrencyCode
    received_amount: Decimal
    penalty_paid: Decimal
    rotation_paid: Decimal
    fund_paid: Decimal
    payment_date: date
    recorded_at: datetime
    fund_allocation_id: str | None

    def __post_init__(self) -> None:
        for value, label in (
            (self.payment_id, "Payment identifier"),
            (self.arrears_id, "Arrears identifier"),
            (self.member_id, "Member identifier"),
            (self.cycle_id, "Cycle identifier"),
        ):
            _text(value, label)
        _positive_integer(self.cycle_number, "Payment cycle number")
        _positive_integer(self.rule_version, "Rule version")
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        for name in (
            "received_amount",
            "penalty_paid",
            "rotation_paid",
            "fund_paid",
        ):
            object.__setattr__(self, name, _money(getattr(self, name), name))
        if self.received_amount == 0:
            raise ValueError("Received amount must be positive.")
        if (
            self.penalty_paid + self.rotation_paid + self.fund_paid
            != self.received_amount
        ):
            raise ValueError("Applied amounts must equal the received amount.")
        if (self.fund_paid > 0) != (self.fund_allocation_id is not None):
            raise ValueError("Fund receipts require exactly one allocation reference.")
        if self.fund_allocation_id is not None:
            _text(self.fund_allocation_id, "Fund allocation identifier")
        if type(self.payment_date) is not date:
            raise TypeError("Payment date must be a calendar date.")
        require_aware_datetime(self.recorded_at, "recorded_at")


@dataclass(frozen=True)
class PenaltyWaiver:
    """Record a governance-approved waiver of an assessed penalty balance."""

    waiver_id: str
    arrears_id: str
    assessment_id: str
    proposal_id: str
    member_id: str
    amount: Decimal
    occurred_at: datetime

    def __post_init__(self) -> None:
        for value, label in (
            (self.waiver_id, "Waiver identifier"),
            (self.arrears_id, "Arrears identifier"),
            (self.assessment_id, "Penalty assessment identifier"),
            (self.proposal_id, "Governance decision identifier"),
            (self.member_id, "Member identifier"),
        ):
            _text(value, label)
        object.__setattr__(self, "amount", _money(self.amount, "Waived amount"))
        if self.amount == 0:
            raise ValueError("Waived amount must be positive.")
        require_aware_datetime(self.occurred_at, "occurred_at")


@dataclass(frozen=True)
class RotationArrearsOffset:
    """Record units redeemed to settle a rotation-pot arrears balance."""

    offset_id: str
    arrears_id: str
    member_id: str
    currency: CurrencyCode
    units: Decimal
    unit_price: Decimal
    amount: Decimal
    valuation_reference: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        for value, label in (
            (self.offset_id, "Offset identifier"),
            (self.arrears_id, "Arrears identifier"),
            (self.member_id, "Member identifier"),
            (self.valuation_reference, "Valuation reference"),
        ):
            _text(value, label)
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        object.__setattr__(self, "units", _money(self.units, "Offset units"))
        object.__setattr__(self, "unit_price", _money(self.unit_price, "Unit price"))
        object.__setattr__(self, "amount", _money(self.amount, "Offset amount"))
        if self.units == 0 or self.unit_price == 0 or self.amount == 0:
            raise ValueError("Offset units, unit price, and amount must be positive.")
        if self.units * self.unit_price != self.amount:
            raise ValueError("Offset amount must equal units multiplied by unit price.")
        require_aware_datetime(self.occurred_at, "occurred_at")


@dataclass(frozen=True)
class ExitArrearsOffset:
    """Record arrears set off against a member's exit entitlement."""

    offset_id: str
    exit_id: str
    arrears_id: str
    member_id: str
    currency: CurrencyCode
    penalty_amount: Decimal
    rotation_amount: Decimal
    fund_amount: Decimal
    occurred_at: datetime

    def __post_init__(self) -> None:
        for value, label in (
            (self.offset_id, "Offset identifier"),
            (self.exit_id, "Exit identifier"),
            (self.arrears_id, "Arrears identifier"),
            (self.member_id, "Member identifier"),
        ):
            _text(value, label)
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        for name in ("penalty_amount", "rotation_amount", "fund_amount"):
            object.__setattr__(self, name, _money(getattr(self, name), name))
        if self.amount == 0:
            raise ValueError("Exit arrears offset must be positive.")
        require_aware_datetime(self.occurred_at, "occurred_at")

    @property
    def amount(self) -> Decimal:
        """Return the total arrears set off in the group's currency units."""
        return self.penalty_amount + self.rotation_amount + self.fund_amount


class HybridArrearsRegistry:
    """Record arrears events and derive their remaining balances."""

    def __init__(self, audit_registry: AuditEventRegistry | None = None) -> None:
        self._audit = audit_registry or AuditEventRegistry()
        self._records: dict[str, ArrearsRecord] = {}
        self._records_by_cycle_member: dict[tuple[str, str], str] = {}
        self._closed_cycles: set[str] = set()
        self._closed_cycle_numbers: set[int] = set()
        self._closed_cycle_numbers_by_id: dict[str, int] = {}
        self._payments: dict[str, PaymentApplication] = {}
        self._elections: dict[str, CatchUpElection] = {}
        self._election_by_arrears: dict[str, str] = {}
        self._forfeitures: dict[str, FundShareForfeiture] = {}
        self._waivers: dict[str, PenaltyWaiver] = {}
        self._waived_assessments: set[str] = set()
        self._waiver_proposals: set[str] = set()
        self._offsets: dict[str, RotationArrearsOffset] = {}
        self._exit_offsets: dict[str, ExitArrearsOffset] = {}
        self._settled_exit_ids: set[str] = set()
        self._used_event_ids: set[str] = set()
        self._audit_event_ids: set[str] = set()

    @classmethod
    def from_snapshot(
        cls,
        snapshot: HybridArrearsSnapshot,
        *,
        allocation_registry: HybridAllocationRegistry,
        unit_ledger: MemberUnitLedger,
        audit_registry: AuditEventRegistry | None = None,
    ) -> HybridArrearsRegistry:
        """Restore arrears histories against matching dependent registries.

        Args:
            snapshot: Validated schema-versioned arrears state.
            allocation_registry: Restored allocation registry referenced by
                fund payment applications.
            unit_ledger: Restored member-unit ledger referenced by unit offsets.
            audit_registry: Optional shared registry that already contains these
                arrears audit events in their recorded order.

        Raises:
            TypeError: If an input has the wrong registry or snapshot type.
            ValueError: If dependent allocation, unit, or audit provenance differs.
        """
        if not isinstance(snapshot, HybridArrearsSnapshot):
            raise TypeError("A hybrid arrears snapshot is required.")
        if not isinstance(allocation_registry, HybridAllocationRegistry):
            raise TypeError("A restored hybrid allocation registry is required.")
        if not isinstance(unit_ledger, MemberUnitLedger):
            raise TypeError("A restored member unit ledger is required.")
        snapshot = HybridArrearsSnapshot(
            schema_version=snapshot.schema_version,
            records=snapshot.records,
            payments=snapshot.payments,
            elections=snapshot.elections,
            forfeitures=snapshot.forfeitures,
            waivers=snapshot.waivers,
            offsets=snapshot.offsets,
            exit_offsets=snapshot.exit_offsets,
            closed_cycles=snapshot.closed_cycles,
            settled_exit_ids=snapshot.settled_exit_ids,
            audit_events=snapshot.audit_events,
        )
        cls._validate_dependencies(snapshot, allocation_registry, unit_ledger)

        if audit_registry is None:
            audit_registry = AuditEventRegistry()
            for event in snapshot.audit_events:
                audit_registry.record(
                    event.event_id,
                    event.event_type,
                    event.aggregate_type,
                    event.aggregate_id,
                    event.occurred_at,
                    event.actor_id,
                    event.source_event,
                    event.details,
                )
        else:
            snapshot_ids = {event.event_id for event in snapshot.audit_events}
            matching_events = tuple(
                event
                for event in audit_registry.all_events()
                if event.event_id in snapshot_ids
            )
            if matching_events != snapshot.audit_events:
                raise ValueError(
                    "Shared audit registry does not contain the snapshot events "
                    "in their recorded order."
                )

        registry = cls(audit_registry)
        registry._records = {record.arrears_id: record for record in snapshot.records}
        registry._records_by_cycle_member = {
            (record.cycle_id, record.member_id): record.arrears_id
            for record in snapshot.records
        }
        registry._closed_cycle_numbers_by_id = dict(snapshot.closed_cycles)
        registry._closed_cycles = set(registry._closed_cycle_numbers_by_id)
        registry._closed_cycle_numbers = set(
            registry._closed_cycle_numbers_by_id.values()
        )
        registry._payments = {item.payment_id: item for item in snapshot.payments}
        registry._elections = {item.election_id: item for item in snapshot.elections}
        registry._election_by_arrears = {
            item.arrears_id: item.election_id for item in snapshot.elections
        }
        registry._forfeitures = {
            item.forfeiture_id: item for item in snapshot.forfeitures
        }
        registry._waivers = {item.waiver_id: item for item in snapshot.waivers}
        registry._waived_assessments = {item.assessment_id for item in snapshot.waivers}
        registry._waiver_proposals = {item.proposal_id for item in snapshot.waivers}
        registry._offsets = {item.offset_id: item for item in snapshot.offsets}
        registry._exit_offsets = {
            item.offset_id: item for item in snapshot.exit_offsets
        }
        registry._settled_exit_ids = set(snapshot.settled_exit_ids)
        registry._used_event_ids = {
            *(item.payment_id for item in snapshot.payments),
            *(item.election_id for item in snapshot.elections),
            *(item.forfeiture_id for item in snapshot.forfeitures),
            *(item.waiver_id for item in snapshot.waivers),
            *(item.offset_id for item in snapshot.offsets),
            *(item.offset_id for item in snapshot.exit_offsets),
        }
        registry._audit_event_ids = {event.event_id for event in snapshot.audit_events}
        return registry

    def snapshot(self) -> HybridArrearsSnapshot:
        """Return immutable arrears histories and closure provenance."""
        audit_events = tuple(
            event
            for event in self._audit.all_events()
            if event.event_id in self._audit_event_ids
        )
        return HybridArrearsSnapshot(
            schema_version=1,
            records=tuple(self._records.values()),
            payments=tuple(self._payments.values()),
            elections=tuple(self._elections.values()),
            forfeitures=tuple(self._forfeitures.values()),
            waivers=tuple(self._waivers.values()),
            offsets=tuple(self._offsets.values()),
            exit_offsets=tuple(self._exit_offsets.values()),
            closed_cycles=tuple(self._closed_cycle_numbers_by_id.items()),
            settled_exit_ids=tuple(sorted(self._settled_exit_ids)),
            audit_events=audit_events,
        )

    @staticmethod
    def _validate_dependencies(
        snapshot: HybridArrearsSnapshot,
        allocation_registry: HybridAllocationRegistry,
        unit_ledger: MemberUnitLedger,
    ) -> None:
        allocation_snapshot = allocation_registry.snapshot()
        allocations_by_id: dict[str, HybridAllocation | PendingHybridAllocation] = {}
        allocations_by_id.update(
            (allocation.allocation_id, allocation)
            for allocation in allocation_snapshot.allocations
        )
        allocations_by_id.update(
            (allocation.allocation_id, allocation)
            for allocation in allocation_snapshot.pending_allocations
        )
        for payment in snapshot.payments:
            if payment.fund_paid == 0:
                continue
            allocation = allocations_by_id.get(payment.fund_allocation_id or "")
            if (
                allocation is None
                or allocation.allocation_type is not AllocationType.CATCH_UP
                or allocation.allocation_id != payment.payment_id
                or allocation.contribution_id != payment.payment_id
                or allocation.member_id != payment.member_id
                or allocation.cycle_id != payment.cycle_id
                or allocation.cycle_number != payment.cycle_number
                or allocation.source_arrears_id != payment.arrears_id
                or allocation.fund_amount != payment.fund_paid
            ):
                raise ValueError(
                    "Catch-up payment does not match its allocation record."
                )

        unit_events = {event.event_id: event for event in unit_ledger.snapshot().events}
        for offset in snapshot.offsets:
            event = unit_events.get(offset.offset_id)
            if (
                not isinstance(event, UnitRedemptionEvent)
                or event.member_id != offset.member_id
                or event.units != offset.units
            ):
                raise ValueError("Unit offset does not match its redemption event.")

    def close_cycle(
        self,
        cycle: ContributionCycle,
        *,
        cycle_number: int,
        rule_version: HybridRuleVersion,
        closed_at: datetime,
    ) -> tuple[ArrearsRecord, ...]:
        """Close a cycle and record each unpaid contribution as arrears.

        Args:
            cycle: Contribution period whose expected and received amounts are
                already recorded.
            cycle_number: Positive ordinal used to resolve effective rules.
            rule_version: Immutable contribution and catch-up policy in force.
            closed_at: Timezone-aware time after the contribution grace period.

        Returns:
            Arrears records created for members with unpaid amounts.
        """
        require_aware_datetime(closed_at, "closed_at")
        _positive_integer(cycle_number, "Cycle number")
        if rule_version.effective_cycle > cycle_number:
            raise ValueError("Hybrid rule version is not effective for this cycle.")
        if (
            cycle.status is CycleStatus.CLOSED
            or cycle.cycle_id in self._closed_cycles
            or cycle_number in self._closed_cycle_numbers
        ):
            raise ValueError(f"Cycle {cycle.cycle_id!r} is already closed.")
        local_close_date = closed_at.astimezone(ZoneInfo(cycle.timezone)).date()
        if local_close_date <= cycle.due_date + timedelta(days=cycle.grace_period_days):
            raise ValueError(
                "A cycle can close only after its contribution grace period."
            )
        if any(
            (cycle.cycle_id, member_id) in self._records_by_cycle_member
            for member_id in cycle.expected_contributions
        ):
            raise ValueError("Arrears already exist for this cycle.")

        currency = CurrencyCode(rule_version.rule.currency)
        if cycle.late_penalty > 0:
            if cycle.penalty_currency != currency:
                raise ValueError(
                    "Penalty currency must match the hybrid rule currency."
                )
            self._require_currency_amount(cycle.late_penalty, currency, "Penalty")
        for member_id, expected in cycle.expected_contributions.items():
            self._require_currency_amount(expected, currency, "Expected contribution")
            contribution = cycle.recorded_contributions.get(member_id)
            if contribution is None:
                continue
            if (
                contribution.member_id != member_id
                or contribution.cycle_id != cycle.cycle_id
            ):
                raise ValueError(
                    "Recorded contribution identity does not match its cycle."
                )
            if contribution.actual_amount is not None:
                self._require_currency_amount(
                    contribution.actual_amount, currency, "Received contribution"
                )
            if contribution.penalty > 0:
                penalty = contribution.penalty_record
                if penalty is None:
                    raise ValueError(
                        "A positive penalty requires its assessment record."
                    )
                if penalty.member_id != member_id or penalty.cycle_id != cycle.cycle_id:
                    raise ValueError("Penalty assessment identity does not match.")
                if penalty.currency != currency:
                    raise ValueError(
                        "Penalty currency must match the hybrid rule currency."
                    )
                self._require_currency_amount(contribution.penalty, currency, "Penalty")

        created: list[ArrearsRecord] = []
        for member_id, expected in cycle.expected_contributions.items():
            contribution = cycle.recorded_contributions.get(member_id)
            if (
                contribution is None
                or contribution.status is ContributionStatus.PENDING
            ):
                contribution = cycle.record_contribution(
                    member_id,
                    None,
                    as_of=closed_at,
                    adjustment=contribution is not None,
                )
            received = contribution.actual_amount or Decimal("0")
            self._require_currency_amount(received, currency, "Received contribution")
            pot_due, fund_due = split_contribution(
                expected, currency, rule_version.rule.fund_share_bps
            )
            pot_paid, fund_paid = self._split_recorded_receipt(
                received,
                expected,
                contribution.status,
                rule_version,
            )
            rotation_amount = max(pot_due - pot_paid, Decimal("0"))
            fund_amount = max(fund_due - fund_paid, Decimal("0"))
            penalty = contribution.penalty_record
            penalty_amount = contribution.penalty
            if penalty_amount > 0:
                if penalty is None:
                    raise ValueError(
                        "A positive penalty requires its assessment record."
                    )
                if penalty.currency != currency:
                    raise ValueError(
                        "Penalty currency must match the hybrid rule currency."
                    )
                self._require_currency_amount(penalty_amount, currency, "Penalty")
                penalty_assessment_id = penalty.assessment_id
                penalty_destination = penalty.destination.value
            else:
                penalty_assessment_id = None
                penalty_destination = None
            if rotation_amount + fund_amount + penalty_amount == 0:
                continue
            arrears_id = _arrears_identifier(cycle.cycle_id, member_id)
            record = ArrearsRecord(
                arrears_id=arrears_id,
                member_id=member_id,
                cycle_id=cycle.cycle_id,
                cycle_number=cycle_number,
                rule_version=rule_version.version,
                currency=currency,
                rotation_amount=rotation_amount,
                fund_amount=fund_amount,
                penalty_amount=penalty_amount,
                penalty_assessment_id=penalty_assessment_id,
                penalty_destination=penalty_destination,
                catch_up_allowed=rule_version.rule.catch_up.allowed,
                catch_up_deadline_cycle=(
                    cycle_number + rule_version.rule.catch_up.deadline_cycles
                ),
                default_outcome=rule_version.rule.catch_up.default_outcome,
                closed_at=closed_at,
            )
            if arrears_id in self._records:
                raise ValueError(f"Arrears {arrears_id!r} are already recorded.")
            created.append(record)

        for record in created:
            self._records[record.arrears_id] = record
            self._records_by_cycle_member[(record.cycle_id, record.member_id)] = (
                record.arrears_id
            )
            self._record_audit(
                "hybrid_arrears_created",
                record.arrears_id,
                record.closed_at,
                record.arrears_id,
                {
                    "member_id": record.member_id,
                    "cycle_number": record.cycle_number,
                    "rule_version": record.rule_version,
                    "currency": str(record.currency),
                    "rotation_amount": str(record.rotation_amount),
                    "fund_amount": str(record.fund_amount),
                    "penalty_amount": str(record.penalty_amount),
                    "penalty_assessment_id": record.penalty_assessment_id,
                    "catch_up_deadline_cycle": record.catch_up_deadline_cycle,
                },
            )
            if not record.catch_up_allowed and record.fund_amount > 0:
                self._forfeit_fund(
                    record,
                    record.fund_amount,
                    ForfeitureCause.CATCH_UP_DISABLED,
                    f"disabled:{record.arrears_id}",
                    record.closed_at,
                )
        self._closed_cycles.add(cycle.cycle_id)
        self._closed_cycle_numbers.add(cycle_number)
        self._closed_cycle_numbers_by_id[cycle.cycle_id] = cycle_number
        cycle.status = CycleStatus.CLOSED
        self._record_audit(
            "hybrid_cycle_closed",
            cycle.cycle_id,
            closed_at,
            cycle.cycle_id,
            {"cycle_number": cycle_number, "arrears_count": len(created)},
        )
        self.apply_catch_up_deadlines(
            current_cycle=cycle_number,
            occurred_at=closed_at,
        )
        return tuple(created)

    def record_catch_up_election(
        self,
        arrears_id: str,
        *,
        election_id: str,
        choice: CatchUpChoice,
        cycle_number: int,
        elected_at: datetime,
    ) -> CatchUpElection:
        """Record a member's catch-up or forfeit choice before its deadline."""
        record = self._record(arrears_id)
        require_aware_datetime(elected_at, "elected_at")
        _positive_integer(cycle_number, "Election cycle number")
        choice = CatchUpChoice(choice)
        if not record.catch_up_allowed:
            raise ValueError("Catch-up is disabled by the applicable group rule.")
        if not record.cycle_number <= cycle_number <= record.catch_up_deadline_cycle:
            raise ValueError("Catch-up election is outside its permitted cycle window.")
        if self.balance_for(arrears_id).fund_amount == 0:
            raise ValueError("No unpaid fund share remains for this arrears record.")
        if arrears_id in self._election_by_arrears:
            raise ValueError("A catch-up election is already recorded.")
        self._ensure_new_id(election_id)
        election = CatchUpElection(
            election_id=election_id,
            arrears_id=arrears_id,
            member_id=record.member_id,
            choice=choice,
            cycle_number=cycle_number,
            elected_at=elected_at,
        )
        self._elections[election_id] = election
        self._election_by_arrears[arrears_id] = election_id
        self._used_event_ids.add(election_id)
        self._record_audit(
            "hybrid_catch_up_elected",
            election_id,
            elected_at,
            arrears_id,
            {"member_id": record.member_id, "choice": choice.value},
        )
        if choice is CatchUpChoice.FORFEIT:
            self._forfeit_fund(
                record,
                self.balance_for(arrears_id).fund_amount,
                ForfeitureCause.MEMBER_ELECTED,
                election_id,
                elected_at,
            )
        return election

    def apply_catch_up_deadlines(
        self,
        *,
        current_cycle: int,
        occurred_at: datetime,
    ) -> tuple[FundShareForfeiture, ...]:
        """Forfeit arrears after the cycle containing their deadline is closed."""
        _positive_integer(current_cycle, "Current cycle")
        require_aware_datetime(occurred_at, "occurred_at")
        if current_cycle not in self._closed_cycle_numbers:
            raise ValueError("Catch-up deadlines apply only after that cycle closes.")
        created: list[FundShareForfeiture] = []
        for record in self._records.values():
            balance = self.balance_for(record.arrears_id).fund_amount
            if balance == 0 or current_cycle < record.catch_up_deadline_cycle:
                continue
            if not record.catch_up_allowed:
                continue
            election_id = self._election_by_arrears.get(record.arrears_id)
            election = self._elections.get(election_id) if election_id else None
            if election is not None and election.choice is CatchUpChoice.FORFEIT:
                continue
            if election is None:
                default_id = f"default:{record.arrears_id}"
                self._ensure_new_id(default_id)
                default = CatchUpElection(
                    election_id=default_id,
                    arrears_id=record.arrears_id,
                    member_id=record.member_id,
                    choice=CatchUpChoice(record.default_outcome.value),
                    cycle_number=current_cycle,
                    elected_at=occurred_at,
                    is_default=True,
                )
                self._elections[default_id] = default
                self._election_by_arrears[record.arrears_id] = default_id
                self._used_event_ids.add(default_id)
                self._record_audit(
                    "hybrid_catch_up_defaulted",
                    default_id,
                    occurred_at,
                    record.arrears_id,
                    {"member_id": record.member_id, "choice": default.choice.value},
                )
                cause = ForfeitureCause.DEFAULTED
            else:
                cause = ForfeitureCause.CATCH_UP_EXPIRED
            forfeiture = self._forfeit_fund(
                record,
                balance,
                cause,
                f"deadline:{record.arrears_id}:{current_cycle}",
                occurred_at,
            )
            created.append(forfeiture)
        return tuple(created)

    def record_payment_application(
        self,
        arrears_id: str,
        *,
        payment_id: str,
        received_amount: Decimal,
        payment_date: date,
        payment_cycle_id: str,
        payment_cycle_number: int,
        rule_version: HybridRuleVersion,
        valuations: Iterable[HybridUnitValuation],
        allocation_registry: HybridAllocationRegistry,
        unit_ledger: MemberUnitLedger,
        recorded_at: datetime,
    ) -> PaymentApplication:
        """Record application of received cash to arrears and allocate catch-up units.

        Payment application follows the recorded penalty and contribution orders.
        A fund share is eligible only after a member catch-up election and is
        priced at the receipt-date valuation; this method never initiates payment.
        """
        record = self._record(arrears_id)
        require_aware_datetime(recorded_at, "recorded_at")
        _positive_integer(payment_cycle_number, "Payment cycle number")
        if rule_version.effective_cycle > payment_cycle_number:
            raise ValueError("Hybrid rule version is not effective for this cycle.")
        if CurrencyCode(rule_version.rule.currency) != record.currency:
            raise ValueError("Payment rule currency must match the arrears currency.")
        if not payment_id.strip() or not payment_cycle_id.strip():
            raise ValueError("Payment and cycle identifiers are required.")
        if type(payment_date) is not date:
            raise TypeError("Payment date must be a calendar date.")
        if payment_id in self._payments:
            raise ValueError(f"Payment {payment_id!r} is already applied.")
        self._ensure_new_id(payment_id)
        self._require_currency_amount(
            received_amount, record.currency, "Received amount", positive=True
        )
        balance = self.balance_for(arrears_id)
        election_id = self._election_by_arrears.get(arrears_id)
        election = self._elections.get(election_id) if election_id else None
        eligible_fund = Decimal("0")
        if (
            election is not None
            and election.choice is CatchUpChoice.CATCH_UP
            and payment_cycle_number <= record.catch_up_deadline_cycle
        ):
            eligible_fund = balance.fund_amount
        eligible_contribution = balance.rotation_amount + eligible_fund
        eligible_total = balance.penalty_amount + eligible_contribution
        if received_amount > eligible_total:
            raise ValueError(
                "Received amount exceeds eligible arrears; "
                "record the excess separately."
            )
        penalty_paid, contribution_paid = self._apply_penalty_order(
            received_amount,
            balance.penalty_amount,
            eligible_contribution,
            rule_version.rule.penalty_order,
            record.currency,
        )
        rotation_paid, fund_paid = self._apply_contribution_order(
            contribution_paid,
            balance.rotation_amount,
            eligible_fund,
            rule_version.rule.contribution_order,
            record.currency,
        )
        if penalty_paid + rotation_paid + fund_paid != received_amount:
            raise ValueError("The payment order could not allocate the full receipt.")

        fund_allocation: HybridAllocation | PendingHybridAllocation | None = None
        if fund_paid > 0:
            fund_allocation = allocation_registry.allocate_catch_up(
                payment_id=payment_id,
                arrears_id=arrears_id,
                member_id=record.member_id,
                cycle_id=payment_cycle_id,
                cycle_number=payment_cycle_number,
                amount=fund_paid,
                payment_date=payment_date,
                rule_version=rule_version,
                valuations=valuations,
                unit_ledger=unit_ledger,
            )
        application = PaymentApplication(
            payment_id=payment_id,
            arrears_id=arrears_id,
            member_id=record.member_id,
            cycle_id=payment_cycle_id,
            cycle_number=payment_cycle_number,
            rule_version=rule_version.version,
            currency=record.currency,
            received_amount=received_amount,
            penalty_paid=penalty_paid,
            rotation_paid=rotation_paid,
            fund_paid=fund_paid,
            payment_date=payment_date,
            recorded_at=recorded_at,
            fund_allocation_id=(
                None if fund_allocation is None else fund_allocation.allocation_id
            ),
        )
        self._payments[payment_id] = application
        self._used_event_ids.add(payment_id)
        self._record_audit(
            "hybrid_arrears_payment_applied",
            payment_id,
            recorded_at,
            arrears_id,
            {
                "member_id": record.member_id,
                "received_amount": str(received_amount),
                "penalty_paid": str(penalty_paid),
                "rotation_paid": str(rotation_paid),
                "fund_paid": str(fund_paid),
                "rule_version": rule_version.version,
                "fund_allocation_id": application.fund_allocation_id,
            },
        )
        return application

    def waive_penalty(
        self,
        arrears_id: str,
        *,
        waiver_id: str,
        proposal_id: str,
        governance: PenaltyWaiverLookup,
        occurred_at: datetime,
    ) -> PenaltyWaiver:
        """Waive an outstanding penalty with an approved governance decision."""
        record = self._record(arrears_id)
        require_aware_datetime(occurred_at, "occurred_at")
        if record.penalty_assessment_id is None:
            raise ValueError("This arrears record has no assessed penalty.")
        if record.penalty_assessment_id in self._waived_assessments:
            raise ValueError("This penalty assessment already has a waiver.")
        if proposal_id in self._waiver_proposals:
            raise ValueError("This governance decision already waived a penalty.")
        effect = governance.approved_penalty_waiver(proposal_id)
        if effect != PenaltyWaiverEffect(
            record.penalty_assessment_id, record.member_id
        ):
            raise ValueError("Approved waiver decision does not match this assessment.")
        amount = self.balance_for(arrears_id).penalty_amount
        if amount == 0:
            raise ValueError("No unpaid penalty remains to waive.")
        self._ensure_new_id(waiver_id)
        waiver = PenaltyWaiver(
            waiver_id=waiver_id,
            arrears_id=arrears_id,
            assessment_id=record.penalty_assessment_id,
            proposal_id=proposal_id,
            member_id=record.member_id,
            amount=amount,
            occurred_at=occurred_at,
        )
        self._waivers[waiver_id] = waiver
        self._waived_assessments.add(record.penalty_assessment_id)
        self._waiver_proposals.add(proposal_id)
        self._used_event_ids.add(waiver_id)
        self._record_audit(
            "hybrid_penalty_waived",
            waiver_id,
            occurred_at,
            arrears_id,
            {
                "member_id": record.member_id,
                "assessment_id": record.penalty_assessment_id,
                "proposal_id": proposal_id,
                "amount": str(amount),
            },
        )
        return waiver

    def offset_rotation_arrears(
        self,
        arrears_id: str,
        *,
        offset_id: str,
        units: Decimal,
        unit_price: Decimal,
        valuation_reference: str,
        occurred_at: datetime,
        unit_ledger: MemberUnitLedger,
    ) -> RotationArrearsOffset:
        """Redeem units explicitly against a member's unpaid rotation amount."""
        record = self._record(arrears_id)
        require_aware_datetime(occurred_at, "occurred_at")
        units = _money(units, "Offset units")
        unit_price = _money(unit_price, "Unit price")
        if units == 0 or unit_price == 0:
            raise ValueError("Offset units and unit price must be positive.")
        if units != _quantize(units, Decimal("0.0001")):
            raise ValueError("Offset units must use four decimal places.")
        amount = _multiply(units, unit_price)
        self._require_currency_amount(amount, record.currency, "Offset amount")
        balance = self.balance_for(arrears_id)
        if balance.rotation_amount == 0:
            raise ValueError("No rotation arrears remain to offset.")
        if amount > balance.rotation_amount:
            raise ValueError("Offset amount exceeds the unpaid rotation arrears.")
        if units > unit_ledger.balance_for(record.member_id):
            raise ValueError("Offset units exceed the member's outstanding units.")
        self._ensure_new_id(offset_id)
        offset = RotationArrearsOffset(
            offset_id=offset_id,
            arrears_id=arrears_id,
            member_id=record.member_id,
            currency=record.currency,
            units=units,
            unit_price=unit_price,
            amount=amount,
            valuation_reference=valuation_reference,
            occurred_at=occurred_at,
        )
        unit_ledger.redeem(record.member_id, units, offset_id)
        self._offsets[offset_id] = offset
        self._used_event_ids.add(offset_id)
        self._record_audit(
            "hybrid_rotation_arrears_offset",
            offset_id,
            occurred_at,
            arrears_id,
            {
                "member_id": record.member_id,
                "units": str(units),
                "unit_price": str(unit_price),
                "amount": str(amount),
                "valuation_reference": valuation_reference,
            },
        )
        return offset

    def redeem_units(
        self,
        member_id: str,
        units: Decimal,
        event_id: str,
        *,
        unit_ledger: MemberUnitLedger,
    ) -> None:
        """Redeem units only when the member has no unpaid rotation arrears."""
        if not member_id.strip():
            raise ValueError("Member identifier is required.")
        if self.rotation_arrears_for(member_id) > 0:
            raise ValueError("Redemption is blocked while rotation arrears remain.")
        unit_ledger.redeem(member_id, units, event_id)

    def apply_exit_setoff(
        self,
        member_id: str,
        exit_id: str,
        *,
        available_amount: Decimal,
        occurred_at: datetime,
    ) -> tuple[ExitArrearsOffset, ...]:
        """Set off exit value against oldest outstanding dues and penalties.

        The available value is applied to each cycle in order, with penalties
        first, then rotation arrears, then fund arrears. Any debt beyond the
        available amount remains outstanding.
        """
        if not member_id.strip() or not exit_id.strip():
            raise ValueError("Member and exit identifiers are required.")
        require_aware_datetime(occurred_at, "occurred_at")
        available_amount = _money(available_amount, "Available exit amount")
        if exit_id in self._settled_exit_ids:
            raise ValueError(f"Exit {exit_id!r} already has an arrears setoff.")
        member_records = sorted(
            (
                record
                for record in self._records.values()
                if record.member_id == member_id
            ),
            key=lambda item: (item.cycle_number, item.arrears_id),
        )
        if member_records and any(
            record.currency != member_records[0].currency for record in member_records
        ):
            raise ValueError("Member arrears must use one currency for exit setoff.")
        if member_records and available_amount != _quantize(
            available_amount, smallest_unit(member_records[0].currency) or Decimal("1")
        ):
            raise ValueError("Available exit amount exceeds currency precision.")

        remaining = available_amount
        planned: list[ExitArrearsOffset] = []
        for record in member_records:
            balance = self.balance_for(record.arrears_id)
            penalty = min(remaining, balance.penalty_amount)
            remaining -= penalty
            rotation = min(remaining, balance.rotation_amount)
            remaining -= rotation
            fund = min(remaining, balance.fund_amount)
            remaining -= fund
            if penalty + rotation + fund == 0:
                continue
            offset_id = _exit_offset_identifier(exit_id, record.arrears_id)
            self._ensure_new_id(offset_id)
            planned.append(
                ExitArrearsOffset(
                    offset_id=offset_id,
                    exit_id=exit_id,
                    arrears_id=record.arrears_id,
                    member_id=member_id,
                    currency=record.currency,
                    penalty_amount=penalty,
                    rotation_amount=rotation,
                    fund_amount=fund,
                    occurred_at=occurred_at,
                )
            )
        for offset in planned:
            self._exit_offsets[offset.offset_id] = offset
            self._used_event_ids.add(offset.offset_id)
            self._record_audit(
                "hybrid_exit_arrears_setoff",
                offset.offset_id,
                occurred_at,
                offset.arrears_id,
                {
                    "exit_id": exit_id,
                    "member_id": member_id,
                    "amount": str(offset.amount),
                    "penalty_amount": str(offset.penalty_amount),
                    "rotation_amount": str(offset.rotation_amount),
                    "fund_amount": str(offset.fund_amount),
                },
            )
        self._settled_exit_ids.add(exit_id)
        return tuple(planned)

    def balance_for(self, arrears_id: str) -> ArrearsBalance:
        """Calculate remaining arrears from the original record and later events."""
        record = self._record(arrears_id)
        payments = tuple(
            item for item in self._payments.values() if item.arrears_id == arrears_id
        )
        offsets = tuple(
            item for item in self._offsets.values() if item.arrears_id == arrears_id
        )
        forfeitures = tuple(
            item for item in self._forfeitures.values() if item.arrears_id == arrears_id
        )
        waivers = tuple(
            item for item in self._waivers.values() if item.arrears_id == arrears_id
        )
        exit_offsets = tuple(
            item
            for item in self._exit_offsets.values()
            if item.arrears_id == arrears_id
        )
        return ArrearsBalance(
            rotation_amount=max(
                record.rotation_amount
                - sum((item.rotation_paid for item in payments), Decimal("0"))
                - sum((item.amount for item in offsets), Decimal("0"))
                - sum((item.rotation_amount for item in exit_offsets), Decimal("0")),
                Decimal("0"),
            ),
            fund_amount=max(
                record.fund_amount
                - sum((item.fund_paid for item in payments), Decimal("0"))
                - sum((item.amount for item in forfeitures), Decimal("0"))
                - sum((item.fund_amount for item in exit_offsets), Decimal("0")),
                Decimal("0"),
            ),
            penalty_amount=max(
                record.penalty_amount
                - sum((item.penalty_paid for item in payments), Decimal("0"))
                - sum((item.amount for item in waivers), Decimal("0"))
                - sum((item.penalty_amount for item in exit_offsets), Decimal("0")),
                Decimal("0"),
            ),
        )

    def rotation_arrears_for(self, member_id: str) -> Decimal:
        """Return the member's unpaid rotation-pot amount across all cycles."""
        return sum(
            (
                self.balance_for(record.arrears_id).rotation_amount
                for record in self._records.values()
                if record.member_id == member_id
            ),
            Decimal("0"),
        )

    def record_for(self, arrears_id: str) -> ArrearsRecord:
        """Return an arrears record by its stable identifier."""
        return self._record(arrears_id)

    def records(self) -> tuple[ArrearsRecord, ...]:
        """Return arrears records in cycle-close order."""
        return tuple(self._records.values())

    def payments(self) -> tuple[PaymentApplication, ...]:
        """Return recorded payment applications in insertion order."""
        return tuple(self._payments.values())

    def elections(self) -> tuple[CatchUpElection, ...]:
        """Return member choices and deadline defaults in insertion order."""
        return tuple(self._elections.values())

    def forfeitures(self) -> tuple[FundShareForfeiture, ...]:
        """Return fund-share forfeitures in insertion order."""
        return tuple(self._forfeitures.values())

    def waivers(self) -> tuple[PenaltyWaiver, ...]:
        """Return approved penalty waivers in insertion order."""
        return tuple(self._waivers.values())

    def offsets(self) -> tuple[RotationArrearsOffset, ...]:
        """Return explicit unit offsets in insertion order."""
        return tuple(self._offsets.values())

    def exit_offsets(self) -> tuple[ExitArrearsOffset, ...]:
        """Return arrears setoffs linked to member exits."""
        return tuple(self._exit_offsets.values())

    def audit_events(self, arrears_id: str) -> tuple[AuditEvent, ...]:
        """Return audit history for one arrears aggregate."""
        self._record(arrears_id)
        return self._audit.events_for("hybrid_arrears", arrears_id)

    def cycle_audit_events(self, cycle_id: str) -> tuple[AuditEvent, ...]:
        """Return the audit event that records a cycle's closure."""
        if cycle_id not in self._closed_cycles:
            raise MissingRecordError(f"Cycle {cycle_id!r} is not closed.")
        return self._audit.events_for("hybrid_arrears", cycle_id)

    def _record(self, arrears_id: str) -> ArrearsRecord:
        try:
            return self._records[arrears_id]
        except KeyError as exc:
            raise MissingRecordError(
                f"No arrears record exists for {arrears_id!r}."
            ) from exc

    def _forfeit_fund(
        self,
        record: ArrearsRecord,
        amount: Decimal,
        cause: ForfeitureCause,
        event_id: str,
        occurred_at: datetime,
    ) -> FundShareForfeiture:
        amount = min(amount, self.balance_for(record.arrears_id).fund_amount)
        if amount <= 0:
            raise ValueError("No unpaid fund share remains to forfeit.")
        forfeiture_id = f"forfeit:{event_id}"
        self._ensure_new_id(forfeiture_id)
        forfeiture = FundShareForfeiture(
            forfeiture_id=forfeiture_id,
            arrears_id=record.arrears_id,
            member_id=record.member_id,
            amount=amount,
            cause=cause,
            occurred_at=occurred_at,
        )
        self._forfeitures[forfeiture_id] = forfeiture
        self._used_event_ids.add(forfeiture_id)
        self._record_audit(
            "hybrid_fund_share_forfeited",
            forfeiture_id,
            occurred_at,
            record.arrears_id,
            {
                "member_id": record.member_id,
                "amount": str(amount),
                "cause": cause.value,
            },
        )
        return forfeiture

    def _record_audit(
        self,
        event_type: str,
        source_id: str,
        occurred_at: datetime,
        arrears_id: str,
        details: dict[str, object],
    ) -> None:
        audit_id = f"hybrid-arrears:{event_type}:{source_id}"
        event = self._audit.record(
            event_id=audit_id,
            event_type=event_type,
            aggregate_type="hybrid_arrears",
            aggregate_id=arrears_id,
            occurred_at=occurred_at,
            actor_id=None,
            source_event=source_id,
            details=details,
        )
        self._audit_event_ids.add(event.event_id)

    def _ensure_new_id(self, event_id: str) -> None:
        if not event_id.strip():
            raise ValueError("Event identifier is required.")
        if event_id in self._used_event_ids:
            raise ValueError(f"Event identifier {event_id!r} is already used.")

    @staticmethod
    def _require_currency_amount(
        value: Decimal,
        currency: CurrencyCode,
        label: str,
        *,
        positive: bool = False,
    ) -> Decimal:
        amount = _money(value, label)
        unit = smallest_unit(currency)
        assert unit is not None
        if amount != _quantize(amount, unit):
            raise ValueError(
                f"{label} exceeds the minor unit precision for {currency}."
            )
        if positive and amount == 0:
            raise ValueError(f"{label} must be positive.")
        return amount

    @classmethod
    def _split_recorded_receipt(
        cls,
        received: Decimal,
        expected: Decimal,
        status: ContributionStatus,
        version: HybridRuleVersion,
    ) -> tuple[Decimal, Decimal]:
        if received == 0:
            return Decimal("0"), Decimal("0")
        rule = version.rule
        if (
            status is ContributionStatus.PARTIAL
            and rule.contribution_order is ContributionPaymentOrder.POT_FIRST
        ):
            expected_pot, _ = split_contribution(
                expected, rule.currency, rule.fund_share_bps
            )
            pot = min(received, expected_pot)
            return pot, received - pot
        return split_contribution(received, rule.currency, rule.fund_share_bps)

    @classmethod
    def _apply_penalty_order(
        cls,
        received: Decimal,
        penalty_due: Decimal,
        contribution_due: Decimal,
        order: PenaltyPaymentOrder,
        currency: CurrencyCode,
    ) -> tuple[Decimal, Decimal]:
        if order is PenaltyPaymentOrder.PENALTY_FIRST:
            penalty_paid = min(received, penalty_due)
            return penalty_paid, received - penalty_paid
        if order is PenaltyPaymentOrder.PENALTY_LAST:
            contribution_paid = min(received, contribution_due)
            return received - contribution_paid, contribution_paid
        total_due = penalty_due + contribution_due
        if total_due == received:
            return penalty_due, contribution_due
        penalty_paid = cls._pro_rata_amount(received, penalty_due, total_due, currency)
        return penalty_paid, received - penalty_paid

    @classmethod
    def _apply_contribution_order(
        cls,
        received: Decimal,
        rotation_due: Decimal,
        fund_due: Decimal,
        order: ContributionPaymentOrder,
        currency: CurrencyCode,
    ) -> tuple[Decimal, Decimal]:
        if received == 0:
            return Decimal("0"), Decimal("0")
        total_due = rotation_due + fund_due
        if received == total_due:
            return rotation_due, fund_due
        if order is ContributionPaymentOrder.POT_FIRST:
            rotation_paid = min(received, rotation_due)
            return rotation_paid, received - rotation_paid
        rotation_paid = cls._pro_rata_amount(
            received, rotation_due, total_due, currency
        )
        fund_paid = received - rotation_paid
        if fund_paid > fund_due:
            fund_paid = fund_due
            rotation_paid = received - fund_paid
        return rotation_paid, fund_paid

    @staticmethod
    def _pro_rata_amount(
        received: Decimal,
        first_due: Decimal,
        total_due: Decimal,
        currency: CurrencyCode,
    ) -> Decimal:
        if total_due == 0:
            return Decimal("0")
        unit = smallest_unit(currency)
        assert unit is not None
        received_units = _minor_units(received, unit)
        first_due_units = _minor_units(first_due, unit)
        total_due_units = _minor_units(total_due, unit)
        return _from_minor_units(
            received_units * first_due_units // total_due_units,
            unit,
        )


def _arrears_identifier(cycle_id: str, member_id: str) -> str:
    identity = json.dumps(
        [cycle_id, member_id], ensure_ascii=True, separators=(",", ":")
    )
    return f"arrears:{identity}"


def _exit_offset_identifier(exit_id: str, arrears_id: str) -> str:
    identity = json.dumps(
        [exit_id, arrears_id], ensure_ascii=True, separators=(",", ":")
    )
    return f"exit-arrears-offset:{identity}"


def _text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required.")


def _positive_integer(value: int, label: str) -> None:
    if type(value) is not int or value < 1:
        raise ValueError(f"{label} must be a positive integer.")


def _money(value: Decimal, label: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{label} must be a Decimal.")
    if not value.is_finite() or value < 0:
        raise ValueError(f"{label} must be finite and non-negative.")
    return value


def _quantize(
    value: Decimal,
    unit: Decimal,
    *,
    rounding: str = ROUND_HALF_EVEN,
) -> Decimal:
    value_exponent = value.as_tuple().exponent
    unit_exponent = unit.as_tuple().exponent
    if not isinstance(value_exponent, int) or not isinstance(unit_exponent, int):
        raise ValueError("Amounts and units must be finite.")
    precision = (
        len(value.as_tuple().digits) + abs(value_exponent) + abs(unit_exponent) + 12
    )
    with localcontext() as context:
        context.prec = max(28, precision)
        return value.quantize(unit, rounding=rounding)


def _minor_units(amount: Decimal, unit: Decimal) -> int:
    unit_exponent = unit.as_tuple().exponent
    amount_exponent = amount.as_tuple().exponent
    if not isinstance(unit_exponent, int) or not isinstance(amount_exponent, int):
        raise ValueError("Amounts and units must be finite.")
    precision = (
        len(amount.as_tuple().digits) + abs(amount_exponent) + abs(unit_exponent) + 12
    )
    with localcontext() as context:
        context.prec = max(28, precision)
        scaled = amount.scaleb(-unit_exponent)
    if scaled != scaled.to_integral_value():
        raise ValueError("Amount is not an exact number of minor units.")
    return int(scaled)


def _from_minor_units(minor_units: int, unit: Decimal) -> Decimal:
    precision = len(str(abs(minor_units))) + len(unit.as_tuple().digits) + 12
    with localcontext() as context:
        context.prec = max(28, precision)
        return Decimal(minor_units) * unit


def _multiply(left: Decimal, right: Decimal) -> Decimal:
    left_exponent = left.as_tuple().exponent
    right_exponent = right.as_tuple().exponent
    if not isinstance(left_exponent, int) or not isinstance(right_exponent, int):
        raise ValueError("Amounts must be finite.")
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


__all__ = [
    "ArrearsBalance",
    "ArrearsRecord",
    "CatchUpChoice",
    "CatchUpElection",
    "ExitArrearsOffset",
    "ForfeitureCause",
    "FundShareForfeiture",
    "HybridArrearsRegistry",
    "PaymentApplication",
    "PenaltyWaiver",
    "RotationArrearsOffset",
]
