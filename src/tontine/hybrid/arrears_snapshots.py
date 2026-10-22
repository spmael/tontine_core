"""Versioned immutable snapshots for hybrid arrears state."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from tontine.audit import AuditEvent

if TYPE_CHECKING:
    from tontine.audit import AuditEventRegistry
    from tontine.investments import MemberUnitLedger

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


@dataclass(frozen=True)
class HybridArrearsSnapshot:
    """Schema-versioned arrears records, subsequent events, and closure state."""

    schema_version: int
    records: tuple[ArrearsRecord, ...]
    payments: tuple[PaymentApplication, ...]
    elections: tuple[CatchUpElection, ...]
    forfeitures: tuple[FundShareForfeiture, ...]
    waivers: tuple[PenaltyWaiver, ...]
    offsets: tuple[RotationArrearsOffset, ...]
    exit_offsets: tuple[ExitArrearsOffset, ...]
    closed_cycles: tuple[tuple[str, int], ...]
    settled_exit_ids: tuple[str, ...]
    audit_events: tuple[AuditEvent, ...]

    def __post_init__(self) -> None:
        from .arrears import (
            ArrearsRecord,
            CatchUpChoice,
            CatchUpElection,
            ExitArrearsOffset,
            ForfeitureCause,
            FundShareForfeiture,
            PaymentApplication,
            PenaltyWaiver,
            RotationArrearsOffset,
            _exit_offset_identifier,
        )

        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError(
                f"Unsupported hybrid arrears snapshot schema: {self.schema_version!r}."
            )
        records = tuple(self.records)
        payments = tuple(self.payments)
        elections = tuple(self.elections)
        forfeitures = tuple(self.forfeitures)
        waivers = tuple(self.waivers)
        offsets = tuple(self.offsets)
        exit_offsets = tuple(self.exit_offsets)
        closed_cycles = tuple(self.closed_cycles)
        settled_exit_ids = tuple(self.settled_exit_ids)
        audit_events = tuple(self.audit_events)
        groups = (
            (records, ArrearsRecord, "ArrearsRecord"),
            (payments, PaymentApplication, "PaymentApplication"),
            (elections, CatchUpElection, "CatchUpElection"),
            (forfeitures, FundShareForfeiture, "FundShareForfeiture"),
            (waivers, PenaltyWaiver, "PenaltyWaiver"),
            (offsets, RotationArrearsOffset, "RotationArrearsOffset"),
            (exit_offsets, ExitArrearsOffset, "ExitArrearsOffset"),
        )
        for values, expected_type, label in groups:
            if any(not isinstance(value, expected_type) for value in values):
                raise TypeError(f"Arrears snapshots require {label} values.")
        if any(not isinstance(event, AuditEvent) for event in audit_events):
            raise TypeError("Arrears snapshots require AuditEvent values.")

        records_by_id = {record.arrears_id: record for record in records}
        if len(records_by_id) != len(records):
            raise ValueError("Arrears identifiers must be unique.")
        cycle_member_keys = [(record.cycle_id, record.member_id) for record in records]
        if len(set(cycle_member_keys)) != len(cycle_member_keys):
            raise ValueError("A cycle and member can have only one arrears record.")

        closed_by_id: dict[str, int] = {}
        closed_numbers: set[int] = set()
        for closed_cycle in closed_cycles:
            if (
                not isinstance(closed_cycle, tuple)
                or len(closed_cycle) != 2
                or not isinstance(closed_cycle[0], str)
                or type(closed_cycle[1]) is not int
                or closed_cycle[1] < 1
                or not closed_cycle[0].strip()
            ):
                raise TypeError(
                    "Closed cycles require (cycle ID, positive number) pairs."
                )
            cycle_id, cycle_number = closed_cycle
            if cycle_id in closed_by_id or cycle_number in closed_numbers:
                raise ValueError("Closed cycle IDs and numbers must be unique.")
            closed_by_id[cycle_id] = cycle_number
            closed_numbers.add(cycle_number)
        if len(closed_by_id) != len(closed_numbers):
            raise ValueError("Closed cycle identifiers and numbers must correspond.")
        for record in records:
            if closed_by_id.get(record.cycle_id) != record.cycle_number:
                raise ValueError("Arrears record does not match its closed cycle.")

        settled_exits: set[str] = set()
        for exit_id in settled_exit_ids:
            if not isinstance(exit_id, str) or not exit_id.strip():
                raise ValueError("Settled exit identifiers are required.")
            if exit_id in settled_exits:
                raise ValueError("Settled exit identifiers must be unique.")
            settled_exits.add(exit_id)

        event_ids = [
            *(item.payment_id for item in payments),
            *(item.election_id for item in elections),
            *(item.forfeiture_id for item in forfeitures),
            *(item.waiver_id for item in waivers),
            *(item.offset_id for item in offsets),
            *(item.offset_id for item in exit_offsets),
        ]
        if len(set(event_ids)) != len(event_ids):
            raise ValueError("Arrears event identifiers must be globally unique.")

        elections_by_arrears: dict[str, CatchUpElection] = {}
        for election in elections:
            record_for_election = records_by_id.get(election.arrears_id)
            if (
                record_for_election is None
                or record_for_election.member_id != election.member_id
                or not record_for_election.catch_up_allowed
                or not record_for_election.cycle_number
                <= election.cycle_number
                <= record_for_election.catch_up_deadline_cycle
            ):
                raise ValueError("Catch-up election references invalid arrears state.")
            if election.arrears_id in elections_by_arrears:
                raise ValueError("An arrears record can have only one election.")
            if election.is_default and (
                election.cycle_number < record.catch_up_deadline_cycle
                or election.choice is not CatchUpChoice.FORFEIT
            ):
                raise ValueError("Deadline defaults must forfeit after the deadline.")
            elections_by_arrears[election.arrears_id] = election

        forfeiture_totals: dict[str, Decimal] = {}
        for forfeiture in forfeitures:
            record_for_forfeiture = records_by_id.get(forfeiture.arrears_id)
            election_for_forfeiture = elections_by_arrears.get(forfeiture.arrears_id)
            if (
                record_for_forfeiture is None
                or record_for_forfeiture.member_id != forfeiture.member_id
            ):
                raise ValueError("Fund forfeiture references invalid arrears state.")
            if forfeiture.cause is ForfeitureCause.CATCH_UP_DISABLED:
                valid_cause = not record_for_forfeiture.catch_up_allowed
            elif forfeiture.cause is ForfeitureCause.MEMBER_ELECTED:
                valid_cause = (
                    election_for_forfeiture is not None
                    and not election_for_forfeiture.is_default
                    and election_for_forfeiture.choice is CatchUpChoice.FORFEIT
                )
            elif forfeiture.cause is ForfeitureCause.DEFAULTED:
                valid_cause = (
                    election_for_forfeiture is not None
                    and election_for_forfeiture.is_default
                    and election_for_forfeiture.choice is CatchUpChoice.FORFEIT
                )
            else:
                valid_cause = (
                    election_for_forfeiture is not None
                    and not election_for_forfeiture.is_default
                    and election_for_forfeiture.choice is CatchUpChoice.CATCH_UP
                    and election_for_forfeiture.cycle_number
                    <= record_for_forfeiture.catch_up_deadline_cycle
                )
            if not valid_cause:
                raise ValueError("Fund forfeiture does not match its election history.")
            forfeiture_totals[record_for_forfeiture.arrears_id] = (
                forfeiture_totals.get(record_for_forfeiture.arrears_id, Decimal("0"))
                + forfeiture.amount
            )

        waiver_assessments: set[str] = set()
        waiver_proposals: set[str] = set()
        for waiver in waivers:
            record_for_waiver = records_by_id.get(waiver.arrears_id)
            if (
                record_for_waiver is None
                or record_for_waiver.member_id != waiver.member_id
                or record_for_waiver.penalty_assessment_id != waiver.assessment_id
                or waiver.assessment_id in waiver_assessments
                or waiver.proposal_id in waiver_proposals
            ):
                raise ValueError("Penalty waiver references invalid arrears state.")
            waiver_assessments.add(waiver.assessment_id)
            waiver_proposals.add(waiver.proposal_id)

        payment_totals: dict[str, list[Decimal]] = {}
        for payment in payments:
            record_for_payment = records_by_id.get(payment.arrears_id)
            if (
                record_for_payment is None
                or record_for_payment.member_id != payment.member_id
                or record_for_payment.currency != payment.currency
            ):
                raise ValueError("Payment references invalid arrears state.")
            if payment.fund_paid > 0:
                election_for_payment = elections_by_arrears.get(payment.arrears_id)
                if (
                    election_for_payment is None
                    or election_for_payment.choice is not CatchUpChoice.CATCH_UP
                    or payment.cycle_number > record_for_payment.catch_up_deadline_cycle
                ):
                    raise ValueError("Fund payment is not eligible under its election.")
            totals = payment_totals.setdefault(
                record_for_payment.arrears_id,
                [Decimal("0"), Decimal("0"), Decimal("0")],
            )
            totals[0] += payment.penalty_paid
            totals[1] += payment.rotation_paid
            totals[2] += payment.fund_paid

        offset_totals: dict[str, Decimal] = {}
        for rotation_offset in offsets:
            record_for_offset = records_by_id.get(rotation_offset.arrears_id)
            if (
                record_for_offset is None
                or record_for_offset.member_id != rotation_offset.member_id
                or record_for_offset.currency != rotation_offset.currency
            ):
                raise ValueError("Unit offset references invalid arrears state.")
            offset_totals[record_for_offset.arrears_id] = (
                offset_totals.get(record_for_offset.arrears_id, Decimal("0"))
                + rotation_offset.amount
            )

        exit_totals: dict[str, list[Decimal]] = {}
        for exit_offset in exit_offsets:
            record_for_exit = records_by_id.get(exit_offset.arrears_id)
            if (
                record_for_exit is None
                or record_for_exit.member_id != exit_offset.member_id
                or record_for_exit.currency != exit_offset.currency
                or exit_offset.exit_id not in settled_exits
                or exit_offset.offset_id
                != _exit_offset_identifier(exit_offset.exit_id, exit_offset.arrears_id)
            ):
                raise ValueError("Exit offset references invalid arrears state.")
            totals = exit_totals.setdefault(
                record_for_exit.arrears_id,
                [Decimal("0"), Decimal("0"), Decimal("0")],
            )
            totals[0] += exit_offset.penalty_amount
            totals[1] += exit_offset.rotation_amount
            totals[2] += exit_offset.fund_amount

        for arrears_id, record in records_by_id.items():
            payments_for_record = payment_totals.get(
                arrears_id, [Decimal("0"), Decimal("0"), Decimal("0")]
            )
            exits_for_record = exit_totals.get(
                arrears_id, [Decimal("0"), Decimal("0"), Decimal("0")]
            )
            if (
                payments_for_record[0]
                + sum(
                    (item.amount for item in waivers if item.arrears_id == arrears_id),
                    Decimal("0"),
                )
                + exits_for_record[0]
                > record.penalty_amount
                or payments_for_record[1]
                + offset_totals.get(arrears_id, Decimal("0"))
                + exits_for_record[1]
                > record.rotation_amount
                or payments_for_record[2]
                + forfeiture_totals.get(arrears_id, Decimal("0"))
                + exits_for_record[2]
                > record.fund_amount
            ):
                raise ValueError(
                    "Arrears event history over-applies its recorded dues."
                )

        audit_ids: set[str] = set()
        valid_audit_types = {
            "hybrid_arrears_created",
            "hybrid_cycle_closed",
            "hybrid_catch_up_elected",
            "hybrid_catch_up_defaulted",
            "hybrid_fund_share_forfeited",
            "hybrid_arrears_payment_applied",
            "hybrid_penalty_waived",
            "hybrid_rotation_arrears_offset",
            "hybrid_exit_arrears_setoff",
        }
        for event in audit_events:
            is_cycle_event = event.event_type == "hybrid_cycle_closed"
            if (
                event.event_id in audit_ids
                or event.aggregate_type != "hybrid_arrears"
                or event.event_type not in valid_audit_types
                or event.source_event is None
                or event.event_id
                != f"hybrid-arrears:{event.event_type}:{event.source_event}"
                or (
                    event.aggregate_id not in closed_by_id
                    if is_cycle_event
                    else event.aggregate_id not in records_by_id
                )
            ):
                raise ValueError("Arrears audit provenance is inconsistent.")
            audit_ids.add(event.event_id)

        object.__setattr__(self, "records", records)
        object.__setattr__(self, "payments", payments)
        object.__setattr__(self, "elections", elections)
        object.__setattr__(self, "forfeitures", forfeitures)
        object.__setattr__(self, "waivers", waivers)
        object.__setattr__(self, "offsets", offsets)
        object.__setattr__(self, "exit_offsets", exit_offsets)
        object.__setattr__(self, "closed_cycles", closed_cycles)
        object.__setattr__(self, "settled_exit_ids", settled_exit_ids)
        object.__setattr__(self, "audit_events", audit_events)

    def restore(
        self,
        *,
        allocation_registry: HybridAllocationRegistry,
        unit_ledger: MemberUnitLedger,
        audit_registry: AuditEventRegistry | None = None,
    ) -> HybridArrearsRegistry:
        """Restore against matching allocation and unit-ledger registries."""
        from .arrears import HybridArrearsRegistry

        return HybridArrearsRegistry.from_snapshot(
            self,
            allocation_registry=allocation_registry,
            unit_ledger=unit_ledger,
            audit_registry=audit_registry,
        )
