"""Versioned immutable snapshots for hybrid domain registries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from tontine.audit import AuditEvent

from .allocation_models import (
    AllocationReversal,
    AllocationType,
    HybridAllocation,
    PendingHybridAllocation,
)
from .rules import HybridRuleVersion

if TYPE_CHECKING:
    from tontine.audit import AuditEventRegistry
    from tontine.investments import MemberUnitLedger

    from .allocation_registry import HybridAllocationRegistry


@dataclass(frozen=True)
class HybridAllocationSnapshot:
    """Schema-versioned allocation records and provenance needed for restore."""

    schema_version: int
    allocations: tuple[HybridAllocation, ...]
    pending_allocations: tuple[PendingHybridAllocation, ...]
    pending_versions: tuple[tuple[str, HybridRuleVersion], ...]
    reversals: tuple[AllocationReversal, ...]
    member_exit_dates: tuple[tuple[str, date, str], ...]
    audit_events: tuple[AuditEvent, ...]

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError(
                f"Unsupported hybrid allocation snapshot schema: "
                f"{self.schema_version!r}."
            )
        allocations = tuple(self.allocations)
        pending = tuple(self.pending_allocations)
        pending_versions = tuple(self.pending_versions)
        reversals = tuple(self.reversals)
        exits = tuple(self.member_exit_dates)
        audit_events = tuple(self.audit_events)
        if any(not isinstance(item, HybridAllocation) for item in allocations):
            raise TypeError("Allocation snapshots require HybridAllocation values.")
        if any(not isinstance(item, PendingHybridAllocation) for item in pending):
            raise TypeError(
                "Allocation snapshots require PendingHybridAllocation values."
            )
        if any(not isinstance(item, AllocationReversal) for item in reversals):
            raise TypeError("Allocation snapshots require AllocationReversal values.")
        if any(not isinstance(item, AuditEvent) for item in audit_events):
            raise TypeError("Allocation snapshots require AuditEvent values.")

        all_records: tuple[HybridAllocation | PendingHybridAllocation, ...] = (
            allocations + pending
        )
        allocation_ids = [item.allocation_id for item in all_records]
        contribution_ids = [item.contribution_id for item in all_records]
        if len(set(allocation_ids)) != len(allocation_ids):
            raise ValueError("Allocation identifiers must be unique in a snapshot.")
        if len(set(contribution_ids)) != len(contribution_ids):
            raise ValueError("Contribution identifiers must be unique in a snapshot.")

        versions_by_contribution: dict[str, HybridRuleVersion] = {}
        for pending_version in pending_versions:
            if (
                not isinstance(pending_version, tuple)
                or len(pending_version) != 2
                or not isinstance(pending_version[0], str)
                or not isinstance(pending_version[1], HybridRuleVersion)
            ):
                raise TypeError(
                    "Pending versions require (contribution ID, rule version) pairs."
                )
            contribution_id, version = pending_version
            if contribution_id in versions_by_contribution:
                raise ValueError(
                    f"Duplicate pending rule version for {contribution_id!r}."
                )
            versions_by_contribution[contribution_id] = version
        if set(versions_by_contribution) != {
            pending_record.contribution_id for pending_record in pending
        }:
            raise ValueError(
                "Every pending allocation requires exactly one rule version."
            )
        for pending_record in pending:
            version = versions_by_contribution[pending_record.contribution_id]
            if (
                pending_record.rule_version != version.version
                or pending_record.payment_order_version != version.version
                or pending_record.cycle_number < version.effective_cycle
                or str(pending_record.currency) != version.rule.currency
            ):
                raise ValueError(
                    "Pending allocation rule version does not match its provenance."
                )

        resolved_by_id = {item.allocation_id: item for item in allocations}
        reversal_by_allocation: dict[str, AllocationReversal] = {}
        reversal_ids: set[str] = set()
        for reversal in reversals:
            if reversal.reversal_id in reversal_ids:
                raise ValueError("Reversal identifiers must be unique in a snapshot.")
            reversal_ids.add(reversal.reversal_id)
            if reversal.reversal_id in set(allocation_ids):
                raise ValueError("Reversal and allocation identifiers must be unique.")
            original = resolved_by_id.get(reversal.original_allocation_id)
            if original is None:
                raise ValueError("A reversal must reference a resolved allocation.")
            if original.allocation_id in reversal_by_allocation:
                raise ValueError("An allocation can have only one reversal.")
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
                raise ValueError("Reversal must exactly offset its allocation.")
            reversal_by_allocation[original.allocation_id] = reversal

        active_source_keys: set[tuple[str, str]] = set()
        for allocation_record in allocations:
            if (
                allocation_record.allocation_type is AllocationType.CONTRIBUTION
                and allocation_record.allocation_id not in reversal_by_allocation
            ):
                key = (allocation_record.cycle_id, allocation_record.member_id)
                if key in active_source_keys:
                    raise ValueError("Active contribution source keys must be unique.")
                active_source_keys.add(key)
        for pending_record in pending:
            if pending_record.allocation_type is AllocationType.CONTRIBUTION:
                key = (pending_record.cycle_id, pending_record.member_id)
                if key in active_source_keys:
                    raise ValueError("Active contribution source keys must be unique.")
                active_source_keys.add(key)

        exit_members: set[str] = set()
        for exit_record in exits:
            if (
                not isinstance(exit_record, tuple)
                or len(exit_record) != 3
                or not isinstance(exit_record[0], str)
                or type(exit_record[1]) is not date
                or not isinstance(exit_record[2], str)
            ):
                raise TypeError(
                    "Member exits require (member ID, date, exit ID) tuples."
                )
            member_id, exit_date, exit_id = exit_record
            if not member_id.strip() or not exit_id.strip():
                raise ValueError("Member and exit identifiers are required.")
            if member_id in exit_members:
                raise ValueError("Member exit records must be unique.")
            exit_members.add(member_id)
            if any(
                record.member_id == member_id and record.receipt_date >= exit_date
                for record in all_records
            ):
                raise ValueError(
                    "A member exit conflicts with a receipt on or after its date."
                )

        audit_ids: set[str] = set()
        for event in audit_events:
            if event.event_id in audit_ids:
                raise ValueError("Audit event identifiers must be unique.")
            audit_ids.add(event.event_id)
            if (
                event.aggregate_type != "hybrid_allocation"
                or event.aggregate_id not in set(allocation_ids)
                or event.event_type
                not in {
                    "hybrid_allocation_pending",
                    "hybrid_allocation_recorded",
                    "hybrid_allocation_resolved",
                    "hybrid_allocation_reversed",
                }
                or event.source_event is None
                or event.event_id
                != f"hybrid-allocation:{event.event_type}:{event.source_event}"
            ):
                raise ValueError("Allocation audit provenance is inconsistent.")

        object.__setattr__(self, "allocations", allocations)
        object.__setattr__(self, "pending_allocations", pending)
        object.__setattr__(self, "pending_versions", pending_versions)
        object.__setattr__(self, "reversals", reversals)
        object.__setattr__(self, "member_exit_dates", exits)
        object.__setattr__(self, "audit_events", audit_events)

    def restore(
        self,
        unit_ledger: MemberUnitLedger,
        audit_registry: AuditEventRegistry | None = None,
    ) -> HybridAllocationRegistry:
        """Restore the registry against its already-restored unit projection."""
        from .allocation_registry import HybridAllocationRegistry

        return HybridAllocationRegistry.from_snapshot(
            self,
            unit_ledger=unit_ledger,
            audit_registry=audit_registry,
        )
