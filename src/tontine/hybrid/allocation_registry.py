"""In-memory registry for recorded hybrid contribution allocations."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal

from tontine.audit import AuditEvent, AuditEventRegistry
from tontine.contributions import Contribution, ContributionCycle, ContributionStatus
from tontine.currencies import CurrencyCode
from tontine.exceptions import MissingRecordError
from tontine.investments import (
    MemberUnitLedger,
    UnitIssueEvent,
    UnitRedemptionEvent,
)

from .allocation_models import (
    AllocationReversal,
    AllocationType,
    HybridAllocation,
    HybridUnitValuation,
    PendingHybridAllocation,
    _price_and_valuation,
    _units_and_residual,
)
from .rules import (
    ContributionPaymentOrder,
    HybridRule,
    HybridRuleVersion,
)
from .snapshots import HybridAllocationSnapshot
from .split import split_contribution


@dataclass(frozen=True)
class _AllocationRequest:
    allocation_id: str
    contribution_id: str
    member_id: str
    cycle_id: str
    cycle_number: int
    version: HybridRuleVersion
    received_amount: Decimal
    receipt_date: date
    pot_amount: Decimal
    fund_amount: Decimal
    allocation_type: AllocationType = AllocationType.CONTRIBUTION
    source_arrears_id: str | None = None


class HybridAllocationRegistry:
    """Keep one resolved or pending allocation for each recorded contribution."""

    def __init__(self, audit_registry: AuditEventRegistry | None = None) -> None:
        self._audit = audit_registry or AuditEventRegistry()
        self._allocations: dict[str, HybridAllocation] = {}
        self._allocations_by_id: dict[str, HybridAllocation] = {}
        self._pending: dict[str, PendingHybridAllocation] = {}
        self._pending_versions: dict[str, HybridRuleVersion] = {}
        self._reversals: dict[str, AllocationReversal] = {}
        self._reversal_ids: set[str] = set()
        self._source_keys: set[tuple[str, str]] = set()
        self._allocation_ids: set[str] = set()
        self._member_exit_dates: dict[str, tuple[date, str]] = {}
        self._audit_event_ids: set[str] = set()

    @classmethod
    def from_snapshot(
        cls,
        snapshot: HybridAllocationSnapshot,
        *,
        unit_ledger: MemberUnitLedger,
        audit_registry: AuditEventRegistry | None = None,
    ) -> HybridAllocationRegistry:
        """Restore registry records without recalculating allocation outcomes.

        Args:
            snapshot: Validated schema-versioned allocation state.
            unit_ledger: Member unit ledger restored from the matching unit
                snapshot.
            audit_registry: Optional shared audit registry that already contains
                this snapshot's audit events in their recorded order.

        Raises:
            TypeError: If snapshot or unit-ledger inputs have the wrong type.
            ValueError: If unit-event provenance does not match the allocations.
        """
        if not isinstance(snapshot, HybridAllocationSnapshot):
            raise TypeError("A hybrid allocation snapshot is required.")
        if not isinstance(unit_ledger, MemberUnitLedger):
            raise TypeError("A restored member unit ledger is required.")
        snapshot = HybridAllocationSnapshot(
            schema_version=snapshot.schema_version,
            allocations=snapshot.allocations,
            pending_allocations=snapshot.pending_allocations,
            pending_versions=snapshot.pending_versions,
            reversals=snapshot.reversals,
            member_exit_dates=snapshot.member_exit_dates,
            audit_events=snapshot.audit_events,
        )
        cls._validate_unit_provenance(snapshot, unit_ledger)

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
            matching_events = tuple(
                event
                for event in audit_registry.all_events()
                if event.event_id in {item.event_id for item in snapshot.audit_events}
            )
            if matching_events != snapshot.audit_events:
                raise ValueError(
                    "Shared audit registry does not contain the snapshot events "
                    "in their recorded order."
                )

        registry = cls(audit_registry)
        registry._allocations = {
            allocation.contribution_id: allocation
            for allocation in snapshot.allocations
        }
        registry._allocations_by_id = {
            allocation.allocation_id: allocation for allocation in snapshot.allocations
        }
        registry._pending = {
            pending.contribution_id: pending for pending in snapshot.pending_allocations
        }
        registry._pending_versions = dict(snapshot.pending_versions)
        registry._reversals = {
            reversal.original_allocation_id: reversal for reversal in snapshot.reversals
        }
        registry._reversal_ids = {
            reversal.reversal_id for reversal in snapshot.reversals
        }
        registry._allocation_ids = {
            allocation.allocation_id for allocation in snapshot.allocations
        } | {pending.allocation_id for pending in snapshot.pending_allocations}
        registry._source_keys = {
            (allocation.cycle_id, allocation.member_id)
            for allocation in snapshot.allocations
            if allocation.allocation_type is AllocationType.CONTRIBUTION
            and allocation.allocation_id not in registry._reversals
        } | {
            (pending.cycle_id, pending.member_id)
            for pending in snapshot.pending_allocations
            if pending.allocation_type is AllocationType.CONTRIBUTION
        }
        registry._member_exit_dates = {
            member_id: (exit_date, exit_id)
            for member_id, exit_date, exit_id in snapshot.member_exit_dates
        }
        registry._audit_event_ids = {event.event_id for event in snapshot.audit_events}
        return registry

    def snapshot(self) -> HybridAllocationSnapshot:
        """Return immutable allocation records and audit provenance."""
        audit_events = tuple(
            event
            for event in self._audit.all_events()
            if event.event_id in self._audit_event_ids
        )
        return HybridAllocationSnapshot(
            schema_version=1,
            allocations=tuple(self._allocations.values()),
            pending_allocations=tuple(self._pending.values()),
            pending_versions=tuple(self._pending_versions.items()),
            reversals=tuple(self._reversals.values()),
            member_exit_dates=tuple(
                (member_id, exit_date, exit_id)
                for member_id, (exit_date, exit_id) in self._member_exit_dates.items()
            ),
            audit_events=audit_events,
        )

    @staticmethod
    def _validate_unit_provenance(
        snapshot: HybridAllocationSnapshot,
        unit_ledger: MemberUnitLedger,
    ) -> None:
        events = unit_ledger.snapshot().events
        events_by_id = {
            event.event_id: (index, event) for index, event in enumerate(events)
        }
        for pending in snapshot.pending_allocations:
            if pending.allocation_id in events_by_id:
                raise ValueError("Pending allocations must not have unit issue events.")
        reversals = {
            reversal.original_allocation_id: reversal for reversal in snapshot.reversals
        }
        for allocation in snapshot.allocations:
            reversal = reversals.get(allocation.allocation_id)
            if allocation.units_issued == 0:
                if allocation.allocation_id in events_by_id:
                    raise ValueError("Zero-unit allocations must not have unit events.")
                if reversal is not None and reversal.reversal_id in events_by_id:
                    raise ValueError("Zero-unit reversals must not have unit events.")
                continue
            issue_entry = events_by_id.get(allocation.allocation_id)
            if issue_entry is None or not isinstance(issue_entry[1], UnitIssueEvent):
                raise ValueError("Allocation unit issue event is missing.")
            if (
                issue_entry[1].member_id != allocation.member_id
                or issue_entry[1].units != allocation.units_issued
            ):
                raise ValueError(
                    "Allocation unit issue event does not match its record."
                )
            if reversal is not None:
                redemption_entry = events_by_id.get(reversal.reversal_id)
                if (
                    redemption_entry is None
                    or not isinstance(redemption_entry[1], UnitRedemptionEvent)
                    or redemption_entry[1].member_id != allocation.member_id
                    or redemption_entry[1].units != allocation.units_issued
                    or redemption_entry[0] <= issue_entry[0]
                ):
                    raise ValueError("Allocation reversal unit event is inconsistent.")

    def record_member_exit(self, member_id: str, exit_date: date, exit_id: str) -> None:
        """Freeze future receipts for a member after an approved exit date."""
        if not member_id.strip() or not exit_id.strip():
            raise ValueError("Member and exit identifiers are required.")
        if type(exit_date) is not date:
            raise TypeError("Exit date must be a calendar date.")
        if member_id in self._member_exit_dates:
            raise ValueError(f"Member {member_id!r} already has a recorded exit.")
        has_later_allocation = any(
            item.member_id == member_id and item.receipt_date >= exit_date
            for item in self._allocations.values()
        )
        has_later_pending_allocation = any(
            item.member_id == member_id and item.receipt_date >= exit_date
            for item in self._pending.values()
        )
        if has_later_allocation or has_later_pending_allocation:
            raise ValueError(
                "Existing contribution receipts on or after the exit date prevent "
                "recording the exit."
            )
        self._member_exit_dates[member_id] = (exit_date, exit_id)

    def allocate(
        self,
        *,
        allocation_id: str,
        contribution_id: str,
        cycle: ContributionCycle,
        member_id: str,
        cycle_number: int,
        rule_version: HybridRuleVersion,
        valuations: Iterable[HybridUnitValuation],
        unit_ledger: MemberUnitLedger,
    ) -> HybridAllocation | PendingHybridAllocation:
        """Allocate a recorded receipt or hold it until a usable valuation exists.

        The contribution identity is the caller-supplied stable identifier, and
        each cycle/member source can be allocated only once. The first
        contribution uses the configured launch price while the ledger has no
        units outstanding.
        """
        request = self._request(
            allocation_id=allocation_id,
            contribution_id=contribution_id,
            cycle=cycle,
            member_id=member_id,
            cycle_number=cycle_number,
            rule_version=rule_version,
        )
        self._ensure_available(request)
        return self._resolve(request, request.receipt_date, valuations, unit_ledger)

    def allocate_catch_up(
        self,
        *,
        payment_id: str,
        arrears_id: str,
        member_id: str,
        cycle_id: str,
        cycle_number: int,
        amount: Decimal,
        payment_date: date,
        rule_version: HybridRuleVersion,
        valuations: Iterable[HybridUnitValuation],
        unit_ledger: MemberUnitLedger,
    ) -> HybridAllocation | PendingHybridAllocation:
        """Allocate a recorded catch-up payment entirely to investment units.

        The payment identifier is unique within the arrears history. The
        allocation uses the payment-date valuation and can be reversed through
        the same append-only path as a regular contribution allocation.
        """
        if not payment_id.strip() or not arrears_id.strip() or not member_id.strip():
            raise ValueError(
                "Catch-up payment, arrears, and member identifiers are required."
            )
        if not cycle_id.strip():
            raise ValueError("Cycle identifier is required.")
        if type(cycle_number) is not int or cycle_number < 1:
            raise ValueError("Cycle number must be a positive integer.")
        if rule_version.effective_cycle > cycle_number:
            raise ValueError("Hybrid rule version is not effective for this cycle.")
        if not isinstance(amount, Decimal) or not amount.is_finite() or amount <= 0:
            raise ValueError("Catch-up amount must be a finite positive Decimal.")
        request = _AllocationRequest(
            allocation_id=payment_id,
            contribution_id=payment_id,
            member_id=member_id,
            cycle_id=cycle_id,
            cycle_number=cycle_number,
            version=rule_version,
            received_amount=amount,
            receipt_date=payment_date,
            pot_amount=Decimal("0"),
            fund_amount=amount,
            allocation_type=AllocationType.CATCH_UP,
            source_arrears_id=arrears_id,
        )
        self._ensure_available(request)
        return self._resolve(request, payment_date, valuations, unit_ledger)

    def resolve_pending(
        self,
        contribution_id: str,
        *,
        allocated_on: date,
        valuations: Iterable[HybridUnitValuation],
        unit_ledger: MemberUnitLedger,
    ) -> HybridAllocation | PendingHybridAllocation:
        """Resolve a pending receipt using a valuation available on its allocation date.

        Args:
            contribution_id: Stable identifier of the pending contribution.
            allocated_on: Date on which the now-valued allocation is resolved.
            valuations: Recorded per-unit valuations available for resolution.
            unit_ledger: Ledger that derives outstanding units.

        Raises:
            MissingRecordError: If the contribution is not pending.
            ValueError: If resolution would predate receipt.
        """
        try:
            pending = self._pending[contribution_id]
        except KeyError as exc:
            raise MissingRecordError(
                f"No pending allocation exists for {contribution_id!r}."
            ) from exc
        if allocated_on < pending.receipt_date:
            raise ValueError("Allocation date must not precede the receipt date.")
        request = _AllocationRequest(
            allocation_id=pending.allocation_id,
            contribution_id=pending.contribution_id,
            member_id=pending.member_id,
            cycle_id=pending.cycle_id,
            cycle_number=pending.cycle_number,
            version=self._pending_versions[contribution_id],
            received_amount=pending.received_amount,
            receipt_date=pending.receipt_date,
            pot_amount=pending.pot_amount,
            fund_amount=pending.fund_amount,
            allocation_type=pending.allocation_type,
            source_arrears_id=pending.source_arrears_id,
        )
        return self._resolve(request, allocated_on, valuations, unit_ledger)

    def replay(
        self, allocation: HybridAllocation, unit_ledger: MemberUnitLedger
    ) -> None:
        """Restore a recorded allocation without resolving rules or valuations."""
        if (
            allocation.contribution_id in self._allocations
            or allocation.contribution_id in self._pending
            or (
                allocation.allocation_type is AllocationType.CONTRIBUTION
                and (allocation.cycle_id, allocation.member_id) in self._source_keys
            )
            or allocation.allocation_id in self._allocation_ids
            or allocation.allocation_id in self._reversal_ids
        ):
            raise ValueError("Contribution already has an allocation.")
        self._ensure_receipt_precedes_exit(
            allocation.member_id, allocation.receipt_date
        )
        self._commit(allocation, unit_ledger, emit_audit=False)

    def reverse(
        self,
        allocation_id: str,
        *,
        reversal_id: str,
        reason: str,
        recorded_at: datetime,
        unit_ledger: MemberUnitLedger,
    ) -> AllocationReversal:
        """Record an immutable offset that cancels one allocation.

        Args:
            allocation_id: Identifier of the resolved allocation to cancel.
            reversal_id: Unique identifier for this reversal event.
            reason: Human-readable explanation for the correction.
            recorded_at: Timezone-aware timestamp for the reversal.
            unit_ledger: Ledger whose member balance will lose the issued units.

        Raises:
            MissingRecordError: If the allocation is unknown.
            ValueError: If it was already reversed or identifiers conflict.
        """
        try:
            original = self._allocations_by_id[allocation_id]
        except KeyError as exc:
            raise MissingRecordError(
                f"Allocation {allocation_id!r} was not found."
            ) from exc
        if allocation_id in self._reversals:
            raise ValueError("Allocation already has a reversal.")
        if reversal_id in self._reversal_ids or reversal_id in self._allocation_ids:
            raise ValueError(f"Reversal identifier {reversal_id!r} is already used.")
        reversal = AllocationReversal(
            reversal_id=reversal_id,
            original_allocation_id=original.allocation_id,
            contribution_id=original.contribution_id,
            member_id=original.member_id,
            reason=reason,
            recorded_at=recorded_at,
            currency=original.currency,
            unit_price=original.unit_price,
            pot_offset=-original.pot_amount,
            fund_offset=-original.fund_amount,
            units_offset=-original.units_issued,
            cash_residual_offset=-original.cash_residual,
        )
        self._apply_reversal(original, reversal, unit_ledger)
        self._audit_event(
            "hybrid_allocation_reversed",
            original.allocation_id,
            reversal.reversal_id,
            reversal.recorded_at,
            {
                "contribution_id": reversal.contribution_id,
                "member_id": reversal.member_id,
                "reason": reversal.reason,
                "currency": str(reversal.currency),
                "pot_offset": str(reversal.pot_offset),
                "fund_offset": str(reversal.fund_offset),
                "units_offset": str(reversal.units_offset),
                "cash_residual_offset": str(reversal.cash_residual_offset),
            },
        )
        return reversal

    def replay_reversal(
        self, reversal: AllocationReversal, unit_ledger: MemberUnitLedger
    ) -> None:
        """Restore a recorded reversal without recalculating its offsets."""
        try:
            original = self._allocations_by_id[reversal.original_allocation_id]
        except KeyError as exc:
            raise MissingRecordError(
                f"Allocation {reversal.original_allocation_id!r} was not found."
            ) from exc
        if original.allocation_id in self._reversals:
            raise ValueError("Allocation already has a reversal.")
        if reversal.reversal_id in self._reversal_ids:
            raise ValueError(f"Reversal {reversal.reversal_id!r} is already recorded.")
        self._apply_reversal(original, reversal, unit_ledger)

    def reversal_for(self, allocation_id: str) -> AllocationReversal:
        """Return the reversal linked to a resolved allocation."""
        try:
            return self._reversals[allocation_id]
        except KeyError as exc:
            raise MissingRecordError(
                f"No reversal exists for allocation {allocation_id!r}."
            ) from exc

    def reversals(self) -> tuple[AllocationReversal, ...]:
        """Return recorded reversals in append order."""
        return tuple(self._reversals.values())

    def audit_events(self, allocation_id: str) -> tuple[AuditEvent, ...]:
        """Return audit history for one allocation and its reversals."""
        return self._audit.events_for("hybrid_allocation", allocation_id)

    def allocation_for(self, contribution_id: str) -> HybridAllocation:
        """Return the resolved allocation for a contribution."""
        try:
            return self._allocations[contribution_id]
        except KeyError as exc:
            raise MissingRecordError(
                f"No resolved allocation exists for {contribution_id!r}."
            ) from exc

    def pending_allocations(self) -> tuple[PendingHybridAllocation, ...]:
        """Return pending allocations in insertion order."""
        return tuple(self._pending.values())

    def allocations(self) -> tuple[HybridAllocation, ...]:
        """Return resolved allocations in insertion order."""
        return tuple(self._allocations.values())

    def _request(
        self,
        *,
        allocation_id: str,
        contribution_id: str,
        cycle: ContributionCycle,
        member_id: str,
        cycle_number: int,
        rule_version: HybridRuleVersion,
    ) -> _AllocationRequest:
        if not allocation_id.strip():
            raise ValueError("Allocation identifier is required.")
        if not contribution_id.strip():
            raise ValueError("Contribution identifier is required.")
        if not member_id.strip():
            raise ValueError("Member identifier is required.")
        if type(cycle_number) is not int or cycle_number < 1:
            raise ValueError("Cycle number must be a positive integer.")
        if rule_version.effective_cycle > cycle_number:
            raise ValueError("Hybrid rule version is not effective for this cycle.")
        if member_id not in cycle.recorded_contributions:
            raise MissingRecordError(
                f"No contribution is recorded for {member_id!r} in {cycle.cycle_id!r}."
            )
        contribution = cycle.recorded_contributions[member_id]
        if (
            contribution.cycle_id != cycle.cycle_id
            or contribution.member_id != member_id
        ):
            raise ValueError("Recorded contribution identity does not match its cycle.")
        received, receipt_date = self._received_contribution(contribution)
        pot, fund = self._split_received(
            received,
            contribution.expected_amount,
            contribution.status,
            rule_version.rule,
        )
        return _AllocationRequest(
            allocation_id=allocation_id,
            contribution_id=contribution_id,
            member_id=member_id,
            cycle_id=cycle.cycle_id,
            cycle_number=cycle_number,
            version=rule_version,
            received_amount=received,
            receipt_date=receipt_date,
            pot_amount=pot,
            fund_amount=fund,
        )

    @staticmethod
    def _split_received(
        received: Decimal,
        expected: Decimal,
        status: ContributionStatus,
        rule: HybridRule,
    ) -> tuple[Decimal, Decimal]:
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

    @staticmethod
    def _received_contribution(contribution: Contribution) -> tuple[Decimal, date]:
        if contribution.status not in {
            ContributionStatus.PAID,
            ContributionStatus.PARTIAL,
            ContributionStatus.LATE,
        }:
            raise ValueError(
                "Only paid, partial, or late contributions can be allocated."
            )
        if contribution.actual_amount is None or contribution.payment_date is None:
            raise ValueError("A recorded receipt amount and payment date are required.")
        if contribution.actual_amount <= 0:
            raise ValueError("A positive recorded receipt is required.")
        return contribution.actual_amount, contribution.payment_date.date()

    def _ensure_available(self, request: _AllocationRequest) -> None:
        self._ensure_receipt_precedes_exit(request.member_id, request.receipt_date)
        source_key = (request.cycle_id, request.member_id)
        if (
            request.contribution_id in self._allocations
            or request.contribution_id in self._pending
            or (
                request.allocation_type is AllocationType.CONTRIBUTION
                and source_key in self._source_keys
            )
            or request.allocation_id in self._allocation_ids
            or request.allocation_id in self._reversal_ids
        ):
            raise ValueError("Contribution already has an allocation.")

    def _ensure_receipt_precedes_exit(self, member_id: str, receipt_date: date) -> None:
        exit_record = self._member_exit_dates.get(member_id)
        if exit_record is not None and receipt_date >= exit_record[0]:
            raise ValueError("No contribution units may be issued on or after exit.")

    def _resolve(
        self,
        request: _AllocationRequest,
        allocated_on: date,
        valuations: Iterable[HybridUnitValuation],
        unit_ledger: MemberUnitLedger,
    ) -> HybridAllocation | PendingHybridAllocation:
        if allocated_on < request.receipt_date:
            raise ValueError("Allocation date must not precede the receipt date.")
        price, valuation_ref, valuation_date, pending_reason = _price_and_valuation(
            rule=request.version.rule,
            valuations=valuations,
            as_of=allocated_on,
            units_outstanding=unit_ledger.total_units,
        )
        if pending_reason is not None:
            is_initial_pending = request.contribution_id not in self._pending
            pending = PendingHybridAllocation(
                allocation_id=request.allocation_id,
                contribution_id=request.contribution_id,
                member_id=request.member_id,
                cycle_id=request.cycle_id,
                cycle_number=request.cycle_number,
                rule_version=request.version.version,
                payment_order_version=request.version.version,
                received_amount=request.received_amount,
                currency=CurrencyCode(request.version.rule.currency),
                receipt_date=request.receipt_date,
                pot_amount=request.pot_amount,
                fund_amount=request.fund_amount,
                reason=pending_reason,
                allocation_type=request.allocation_type,
                source_arrears_id=request.source_arrears_id,
            )
            self._pending[request.contribution_id] = pending
            self._pending_versions[request.contribution_id] = request.version
            if request.allocation_type is AllocationType.CONTRIBUTION:
                self._source_keys.add((request.cycle_id, request.member_id))
            self._allocation_ids.add(request.allocation_id)
            if is_initial_pending:
                self._audit_event(
                    "hybrid_allocation_pending",
                    request.allocation_id,
                    request.contribution_id,
                    self._audit_time(request.receipt_date),
                    self._allocation_details(pending),
                )
            return pending
        units, residual = _units_and_residual(request.fund_amount, price)
        allocation = HybridAllocation(
            allocation_id=request.allocation_id,
            contribution_id=request.contribution_id,
            member_id=request.member_id,
            cycle_id=request.cycle_id,
            cycle_number=request.cycle_number,
            rule_version=request.version.version,
            payment_order_version=request.version.version,
            received_amount=request.received_amount,
            currency=CurrencyCode(request.version.rule.currency),
            receipt_date=request.receipt_date,
            allocated_on=allocated_on,
            valuation_reference=valuation_ref,
            valuation_date=valuation_date,
            unit_price=price,
            pot_amount=request.pot_amount,
            fund_amount=request.fund_amount,
            units_issued=units,
            cash_residual=residual,
            allocation_type=request.allocation_type,
            source_arrears_id=request.source_arrears_id,
        )
        self._commit(allocation, unit_ledger)
        return allocation

    def _commit(
        self,
        allocation: HybridAllocation,
        unit_ledger: MemberUnitLedger,
        *,
        emit_audit: bool = True,
    ) -> None:
        was_pending = allocation.contribution_id in self._pending
        if allocation.units_issued > 0:
            unit_ledger.issue_units(
                allocation.member_id,
                allocation.units_issued,
                allocation.allocation_id,
            )
        self._allocations[allocation.contribution_id] = allocation
        self._allocations_by_id[allocation.allocation_id] = allocation
        if allocation.allocation_type is AllocationType.CONTRIBUTION:
            self._source_keys.add((allocation.cycle_id, allocation.member_id))
        self._allocation_ids.add(allocation.allocation_id)
        self._pending.pop(allocation.contribution_id, None)
        self._pending_versions.pop(allocation.contribution_id, None)
        if emit_audit:
            self._audit_event(
                (
                    "hybrid_allocation_resolved"
                    if was_pending
                    else "hybrid_allocation_recorded"
                ),
                allocation.allocation_id,
                allocation.contribution_id,
                self._audit_time(allocation.allocated_on),
                self._allocation_details(allocation),
            )

    def _apply_reversal(
        self,
        original: HybridAllocation,
        reversal: AllocationReversal,
        unit_ledger: MemberUnitLedger,
    ) -> None:
        if original.allocation_id in self._reversals:
            raise ValueError("Allocation already has a reversal.")
        if reversal.reversal_id in self._reversal_ids or (
            reversal.reversal_id in self._allocation_ids
        ):
            raise ValueError(
                f"Reversal identifier {reversal.reversal_id!r} is already used."
            )
        if (
            reversal.contribution_id != original.contribution_id
            or reversal.member_id != original.member_id
            or reversal.currency != original.currency
            or reversal.unit_price != original.unit_price
            or reversal.pot_offset != -original.pot_amount
            or reversal.fund_offset != -original.fund_amount
            or reversal.units_offset != -original.units_issued
            or reversal.cash_residual_offset != -original.cash_residual
        ):
            raise ValueError("Reversal must exactly offset the original allocation.")
        if original.units_issued > 0:
            unit_ledger.redeem(
                original.member_id,
                original.units_issued,
                reversal.reversal_id,
            )
        self._reversals[original.allocation_id] = reversal
        self._reversal_ids.add(reversal.reversal_id)
        if original.allocation_type is AllocationType.CONTRIBUTION:
            self._source_keys.discard((original.cycle_id, original.member_id))

    @staticmethod
    def _audit_time(effective_date: date) -> datetime:
        """Normalize date-only allocation events to UTC midnight."""
        return datetime.combine(effective_date, time.min, tzinfo=UTC)

    @staticmethod
    def _allocation_details(
        allocation: HybridAllocation | PendingHybridAllocation,
    ) -> dict[str, object]:
        details: dict[str, object] = {
            "allocation_id": allocation.allocation_id,
            "contribution_id": allocation.contribution_id,
            "member_id": allocation.member_id,
            "cycle_id": allocation.cycle_id,
            "cycle_number": allocation.cycle_number,
            "rule_version": allocation.rule_version,
            "payment_order_version": allocation.payment_order_version,
            "received_amount": str(allocation.received_amount),
            "currency": str(allocation.currency),
            "receipt_date": allocation.receipt_date.isoformat(),
            "pot_amount": str(allocation.pot_amount),
            "fund_amount": str(allocation.fund_amount),
            "allocation_type": allocation.allocation_type.value,
            "source_arrears_id": allocation.source_arrears_id,
        }
        if isinstance(allocation, PendingHybridAllocation):
            details["reason"] = allocation.reason.value
        else:
            details.update(
                {
                    "allocated_on": allocation.allocated_on.isoformat(),
                    "valuation_reference": allocation.valuation_reference,
                    "valuation_date": (
                        None
                        if allocation.valuation_date is None
                        else allocation.valuation_date.isoformat()
                    ),
                    "unit_price": str(allocation.unit_price),
                    "units_issued": str(allocation.units_issued),
                    "cash_residual": str(allocation.cash_residual),
                }
            )
        return details

    def _audit_event(
        self,
        event_type: str,
        allocation_id: str,
        source_event: str,
        occurred_at: datetime,
        details: dict[str, object],
    ) -> None:
        event_id = f"hybrid-allocation:{event_type}:{source_event}"
        event = self._audit.record(
            event_id,
            event_type,
            "hybrid_allocation",
            allocation_id,
            occurred_at,
            None,
            source_event,
            details,
        )
        self._audit_event_ids.add(event.event_id)
