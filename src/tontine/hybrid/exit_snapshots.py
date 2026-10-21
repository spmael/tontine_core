"""Versioned immutable snapshots for hybrid exit state."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from tontine.audit import AuditEvent
from tontine.governance import MemberExitType

if TYPE_CHECKING:
    from tontine.audit import AuditEventRegistry
    from tontine.investments import MemberUnitLedger

    from .allocation_registry import HybridAllocationRegistry
    from .arrears import HybridArrearsRegistry
    from .exit import HybridExitRegistry
    from .exit_models import ExitQueueReport, HybridExit


@dataclass(frozen=True)
class HybridExitSnapshot:
    """Schema-versioned exit records, queue reports, and audit provenance."""

    schema_version: int
    exits: tuple[HybridExit, ...]
    queue_reports: tuple[ExitQueueReport, ...]
    audit_events: tuple[AuditEvent, ...]

    def __post_init__(self) -> None:
        from .exit_models import ExitQueueReport, ExitStatus, HybridExit

        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError(
                f"Unsupported hybrid exit snapshot schema: {self.schema_version!r}."
            )
        exits = tuple(self.exits)
        reports = tuple(self.queue_reports)
        audit_events = tuple(self.audit_events)
        if any(not isinstance(item, HybridExit) for item in exits):
            raise TypeError("Exit snapshots require HybridExit values.")
        if any(not isinstance(item, ExitQueueReport) for item in reports):
            raise TypeError("Exit snapshots require ExitQueueReport values.")
        if any(not isinstance(item, AuditEvent) for item in audit_events):
            raise TypeError("Exit snapshots require AuditEvent values.")

        exits_by_id = {item.exit_id: item for item in exits}
        if len(exits_by_id) != len(exits):
            raise ValueError("Exit identifiers must be unique in a snapshot.")
        member_ids = [item.member_id for item in exits]
        if len(set(member_ids)) != len(member_ids):
            raise ValueError("A member can have only one recorded exit.")
        reports_by_id = {item.report_id: item for item in reports}
        if len(reports_by_id) != len(reports):
            raise ValueError("Queue report identifiers must be unique.")

        last_report_entries = {}
        for report in reports:
            if any(
                entry.position != index
                for index, entry in enumerate(report.entries, 1)
            ):
                raise ValueError("Queue report positions must be contiguous.")
            queued_seen = False
            payable_total = Decimal("0")
            sort_keys = []
            for entry in report.entries:
                exit_record = exits_by_id.get(entry.exit_id)
                if (
                    exit_record is None
                    or exit_record.member_id != entry.member_id
                    or exit_record.settlement is None
                    or exit_record.settlement.currency != report.currency
                    or exit_record.settlement.net_amount != entry.amount
                    or entry.amount <= 0
                    or exit_record.payout_due_date > report.created_at.date()
                ):
                    raise ValueError("Queue entry does not match its exit record.")
                sort_keys.append(
                    (
                        exit_record.exit_date,
                        exit_record.requested_at,
                        exit_record.exit_id,
                    )
                )
                if entry.status is ExitStatus.QUEUED:
                    queued_seen = True
                elif queued_seen:
                    raise ValueError("A payable exit cannot follow an unfunded exit.")
                else:
                    payable_total += entry.amount
                last_report_entries[entry.exit_id] = entry
            if sort_keys != sorted(sort_keys):
                raise ValueError("Queue entries must retain FIFO order.")
            if payable_total > report.liquidity_cap:
                raise ValueError("Queue report exceeds its liquidity cap.")

        for exit_record in exits:
            settlement = exit_record.settlement
            if exit_record.status is ExitStatus.PENDING_VALUATION:
                if settlement is not None:
                    raise ValueError("Pending valuation exits cannot have settlements.")
                if any(
                    reference is not None
                    for reference in (
                        exit_record.estate_proof_reference,
                        exit_record.consignment_reference,
                        exit_record.external_payment_reference,
                    )
                ) or exit_record.queue_position is not None:
                    raise ValueError("Pending valuation exit contains later state.")
                continue
            if settlement is None:
                raise ValueError("Resolved exit state requires a settlement.")
            if settlement.net_amount < 0:
                expected_statuses = {ExitStatus.AMOUNT_OWED}
            elif settlement.net_amount == 0:
                expected_statuses = {ExitStatus.NO_PAYOUT}
            elif exit_record.exit_type is MemberExitType.DEATH:
                expected_statuses = {
                    ExitStatus.HELD_FOR_ESTATE,
                    ExitStatus.QUEUED,
                    ExitStatus.PAYABLE,
                    ExitStatus.CONSIGNED,
                    ExitStatus.PAID_EXTERNALLY,
                }
            else:
                expected_statuses = {
                    ExitStatus.QUEUED,
                    ExitStatus.PAYABLE,
                    ExitStatus.CONSIGNED,
                    ExitStatus.PAID_EXTERNALLY,
                }
            if exit_record.status not in expected_statuses:
                raise ValueError("Exit status is inconsistent with its settlement.")
            if exit_record.status is ExitStatus.HELD_FOR_ESTATE and (
                exit_record.estate_proof_reference is not None
            ):
                raise ValueError("Estate-held exits cannot already have proof.")
            if exit_record.estate_proof_reference is not None and (
                exit_record.exit_type is not MemberExitType.DEATH
                or settlement.net_amount <= 0
            ):
                raise ValueError("Estate proof does not match a positive death exit.")
            if (
                exit_record.exit_type is MemberExitType.DEATH
                and settlement.net_amount > 0
                and exit_record.estate_proof_reference is None
                and (
                    exit_record.status
                    in {
                        ExitStatus.QUEUED,
                        ExitStatus.PAYABLE,
                        ExitStatus.PAID_EXTERNALLY,
                    }
                    or exit_record.queue_position is not None
                )
            ):
                raise ValueError("A released death entitlement requires estate proof.")
            if (exit_record.status is ExitStatus.CONSIGNED) != (
                exit_record.consignment_reference is not None
            ):
                raise ValueError("Consignment reference does not match exit status.")
            if (exit_record.status is ExitStatus.PAID_EXTERNALLY) != (
                exit_record.external_payment_reference is not None
            ):
                raise ValueError("Payment reference does not match exit status.")
            if exit_record.queue_position is not None:
                latest = last_report_entries.get(exit_record.exit_id)
                if (
                    latest is None
                    or latest.position != exit_record.queue_position
                    or (
                        exit_record.status
                        in {ExitStatus.QUEUED, ExitStatus.PAYABLE}
                        and latest.status is not exit_record.status
                    )
                    or (
                        exit_record.status is ExitStatus.PAID_EXTERNALLY
                        and latest.status is not ExitStatus.PAYABLE
                    )
                ):
                    raise ValueError("Exit queue position does not match its report.")
            elif exit_record.exit_id in last_report_entries:
                raise ValueError("Queued exit is missing its recorded queue position.")

        audit_by_exit_type: dict[tuple[str, str], list[AuditEvent]] = {}
        audit_ids: set[str] = set()
        valid_audit_types = {
            "hybrid_member_exit_recorded",
            "hybrid_exit_settled",
            "hybrid_exit_estate_proof_recorded",
            "hybrid_exit_consigned",
            "hybrid_exit_external_payment_recorded",
            "hybrid_exit_queue_reported",
        }
        for event in audit_events:
            aggregate_exists = (
                event.aggregate_id in reports_by_id
                if event.event_type == "hybrid_exit_queue_reported"
                else event.aggregate_id in exits_by_id
            )
            if (
                event.event_id in audit_ids
                or event.aggregate_type != "hybrid_exit"
                or event.event_type not in valid_audit_types
                or not aggregate_exists
                or event.event_id
                != f"hybrid-exit:{event.event_type}:{event.aggregate_id}"
                or (
                    event.event_type == "hybrid_exit_queue_reported"
                    and event.source_event is not None
                )
                or (
                    event.event_type != "hybrid_exit_queue_reported"
                    and event.source_event is None
                )
            ):
                raise ValueError("Exit audit provenance is inconsistent.")
            audit_ids.add(event.event_id)
            audit_by_exit_type.setdefault(
                (event.aggregate_id, event.event_type), []
            ).append(event)

        for exit_record in exits:
            recorded_events = audit_by_exit_type.get(
                (exit_record.exit_id, "hybrid_member_exit_recorded"), []
            )
            settled_events = audit_by_exit_type.get(
                (exit_record.exit_id, "hybrid_exit_settled"), []
            )
            if (
                len(recorded_events) != 1
                or recorded_events[0].source_event != exit_record.proposal_id
                or (exit_record.settlement is None and settled_events)
                or (
                    exit_record.settlement is not None and len(settled_events) != 1
                )
                or (
                    settled_events
                    and settled_events[0].source_event != exit_record.proposal_id
                )
            ):
                raise ValueError("Exit audit history does not match its record.")
            estate_events = audit_by_exit_type.get(
                (exit_record.exit_id, "hybrid_exit_estate_proof_recorded"), []
            )
            if (
                (
                    exit_record.estate_proof_reference is None
                    and estate_events
                )
                or (
                    exit_record.estate_proof_reference is not None
                    and (
                    len(estate_events) != 1
                    or estate_events[0].source_event
                    != exit_record.estate_proof_reference
                    )
                )
            ):
                raise ValueError(
                    "Estate-proof audit history does not match its record."
                )
            consignment_events = audit_by_exit_type.get(
                (exit_record.exit_id, "hybrid_exit_consigned"), []
            )
            if (
                (
                    exit_record.consignment_reference is None
                    and consignment_events
                )
                or (
                    exit_record.consignment_reference is not None
                    and (
                    len(consignment_events) != 1
                    or consignment_events[0].source_event
                    != exit_record.consignment_reference
                    )
                )
            ):
                raise ValueError("Consignment audit history does not match its record.")
            payment_events = audit_by_exit_type.get(
                (exit_record.exit_id, "hybrid_exit_external_payment_recorded"), []
            )
            if (
                (
                    exit_record.external_payment_reference is None
                    and payment_events
                )
                or (
                    exit_record.external_payment_reference is not None
                    and (
                    len(payment_events) != 1
                    or payment_events[0].source_event
                    != exit_record.external_payment_reference
                    )
                )
            ):
                raise ValueError("Payment audit history does not match its record.")
        for report in reports:
            events = audit_by_exit_type.get(
                (report.report_id, "hybrid_exit_queue_reported"), []
            )
            if len(events) != 1:
                raise ValueError("Every queue report requires one audit event.")

        object.__setattr__(self, "exits", exits)
        object.__setattr__(self, "queue_reports", reports)
        object.__setattr__(self, "audit_events", audit_events)

    def restore(
        self,
        *,
        allocation_registry: HybridAllocationRegistry,
        arrears_registry: HybridArrearsRegistry,
        unit_ledger: MemberUnitLedger,
        audit_registry: AuditEventRegistry | None = None,
    ) -> HybridExitRegistry:
        """Restore exit state against matching allocation, arrears, and unit data."""
        from .exit import HybridExitRegistry

        return HybridExitRegistry.from_snapshot(
            self,
            allocation_registry=allocation_registry,
            arrears_registry=arrears_registry,
            unit_ledger=unit_ledger,
            audit_registry=audit_registry,
        )
