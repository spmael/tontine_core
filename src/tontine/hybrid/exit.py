"""Member exit settlement and payout-entitlement records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal, localcontext

from tontine._datetime import require_aware_datetime
from tontine.audit import AuditEvent, AuditEventRegistry
from tontine.classic import ClassicPayout
from tontine.contributions import ContributionCycle
from tontine.currencies import CurrencyCode
from tontine.exceptions import MissingRecordError
from tontine.governance import MemberExitEffect, MemberExitType
from tontine.investments import MemberUnitLedger, UnitRedemptionEvent

from ._exit_calculations import excess_pot_received, first_eligible_valuation
from .allocation import HybridAllocationRegistry, HybridUnitValuation
from .arrears import ExitArrearsOffset, HybridArrearsRegistry
from .exit_models import (
    ExitGovernanceLookup,
    ExitQueueEntry,
    ExitQueueReport,
    ExitSettlement,
    ExitStatus,
    HybridExit,
    _add_months,
    _currency_amount,
    _identifier,
    _multiply,
    _net_amount,
    _sum_amounts,
)
from .exit_snapshots import HybridExitSnapshot
from .rules import HybridRuleSchedule, LegalForm


class HybridExitRegistry:
    """Record approved member exits without initiating external payments."""

    def __init__(
        self,
        allocation_registry: HybridAllocationRegistry,
        arrears_registry: HybridArrearsRegistry,
        unit_ledger: MemberUnitLedger,
        audit_registry: AuditEventRegistry | None = None,
    ) -> None:
        self._allocations = allocation_registry
        self._arrears = arrears_registry
        self._units = unit_ledger
        self._audit = audit_registry or AuditEventRegistry()
        self._exits: dict[str, HybridExit] = {}
        self._reports: dict[str, ExitQueueReport] = {}
        self._audit_event_ids: set[str] = set()

    @classmethod
    def from_snapshot(
        cls,
        snapshot: HybridExitSnapshot,
        *,
        allocation_registry: HybridAllocationRegistry,
        arrears_registry: HybridArrearsRegistry,
        unit_ledger: MemberUnitLedger,
        audit_registry: AuditEventRegistry | None = None,
    ) -> HybridExitRegistry:
        """Restore recorded exits without replaying governance or settlements.

        Args:
            snapshot: Validated schema-versioned exit state.
            allocation_registry: Restored allocation registry containing matching
                member-exit freezes.
            arrears_registry: Restored arrears registry containing matching exit
                setoffs.
            unit_ledger: Restored member-unit event history.
            audit_registry: Optional shared registry that already contains these
                exit audit events in their recorded order.

        Raises:
            TypeError: If a supplied registry or snapshot has the wrong type.
            ValueError: If cross-registry provenance does not match.
        """
        if not isinstance(snapshot, HybridExitSnapshot):
            raise TypeError("A hybrid exit snapshot is required.")
        if not isinstance(allocation_registry, HybridAllocationRegistry):
            raise TypeError("A restored hybrid allocation registry is required.")
        if not isinstance(arrears_registry, HybridArrearsRegistry):
            raise TypeError("A restored hybrid arrears registry is required.")
        if not isinstance(unit_ledger, MemberUnitLedger):
            raise TypeError("A restored member unit ledger is required.")
        snapshot = HybridExitSnapshot(
            schema_version=snapshot.schema_version,
            exits=snapshot.exits,
            queue_reports=snapshot.queue_reports,
            audit_events=snapshot.audit_events,
        )
        cls._validate_dependencies(
            snapshot,
            allocation_registry,
            arrears_registry,
            unit_ledger,
        )
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

        registry = cls(
            allocation_registry,
            arrears_registry,
            unit_ledger,
            audit_registry,
        )
        registry._exits = {item.exit_id: item for item in snapshot.exits}
        registry._reports = {
            item.report_id: item for item in snapshot.queue_reports
        }
        registry._audit_event_ids = {
            event.event_id for event in snapshot.audit_events
        }
        return registry

    def snapshot(self) -> HybridExitSnapshot:
        """Return immutable exit records, queue reports, and audit provenance."""
        audit_events = tuple(
            event
            for event in self._audit.all_events()
            if event.event_id in self._audit_event_ids
        )
        return HybridExitSnapshot(
            schema_version=1,
            exits=tuple(self._exits.values()),
            queue_reports=tuple(self._reports.values()),
            audit_events=audit_events,
        )

    @staticmethod
    def _validate_dependencies(
        snapshot: HybridExitSnapshot,
        allocation_registry: HybridAllocationRegistry,
        arrears_registry: HybridArrearsRegistry,
        unit_ledger: MemberUnitLedger,
    ) -> None:
        allocation_snapshot = allocation_registry.snapshot()
        expected_freezes = {
            exit_record.member_id: (exit_record.exit_date, exit_record.exit_id)
            for exit_record in snapshot.exits
        }
        actual_freezes = {
            member_id: (exit_date, exit_id)
            for member_id, exit_date, exit_id in allocation_snapshot.member_exit_dates
        }
        if actual_freezes != expected_freezes:
            raise ValueError("Exit records do not match allocation exit freezes.")

        arrears_snapshot = arrears_registry.snapshot()
        settled_exit_ids = {
            exit_record.exit_id
            for exit_record in snapshot.exits
            if exit_record.settlement is not None
        }
        if set(arrears_snapshot.settled_exit_ids) != settled_exit_ids:
            raise ValueError("Exit records do not match arrears settlement IDs.")
        offsets_by_exit: dict[str, list[ExitArrearsOffset]] = {}
        for offset in arrears_snapshot.exit_offsets:
            offsets_by_exit.setdefault(offset.exit_id, []).append(offset)
        for exit_record in snapshot.exits:
            settlement = exit_record.settlement
            offsets = offsets_by_exit.get(exit_record.exit_id, [])
            if settlement is None:
                if offsets:
                    raise ValueError("Pending exits cannot have arrears setoffs.")
                continue
            available = min(
                max(
                    _net_amount(
                        settlement.gross_unit_value,
                        settlement.exit_fee,
                    ),
                    Decimal("0"),
                ),
                _sum_amounts(
                    settlement.unpaid_penalties,
                    settlement.unpaid_rotation_dues,
                    settlement.unpaid_fund_dues,
                ),
            )
            penalty = min(available, settlement.unpaid_penalties)
            remaining = _net_amount(available, penalty)
            rotation = min(remaining, settlement.unpaid_rotation_dues)
            remaining = _net_amount(remaining, rotation)
            fund = min(remaining, settlement.unpaid_fund_dues)
            if (
                sum((item.penalty_amount for item in offsets), Decimal("0"))
                != penalty
                or sum((item.rotation_amount for item in offsets), Decimal("0"))
                != rotation
                or sum((item.fund_amount for item in offsets), Decimal("0")) != fund
            ):
                raise ValueError(
                    "Exit arrears setoffs do not match the recorded settlement."
                )

        unit_events = {
            event.event_id: event for event in unit_ledger.snapshot().events
        }
        for exit_record in snapshot.exits:
            redemption_id = f"hybrid-exit:{exit_record.exit_id}:redeem"
            event = unit_events.get(redemption_id)
            settlement = exit_record.settlement
            if settlement is None:
                if event is not None:
                    raise ValueError("Pending exits cannot have redemption events.")
            elif (
                not isinstance(event, UnitRedemptionEvent)
                or event.member_id != exit_record.member_id
                or event.units != settlement.units_redeemed
            ):
                raise ValueError("Exit settlement does not match its unit event.")

    def record_exit(
        self,
        *,
        exit_id: str,
        proposal_id: str,
        governance: ExitGovernanceLookup,
        rules: HybridRuleSchedule,
        payout_due_date: date,
        requested_at: datetime,
        deferral_proposal_id: str | None = None,
    ) -> HybridExit:
        """Record an approved exit and freeze subsequent unit allocation.

        ``payout_due_date`` is the cycle-end date supplied by the caller. An
        approved extension may move it beyond 12 months, but never beyond 24.
        """
        _identifier(exit_id, "Exit identifier")
        _identifier(proposal_id, "Governance decision identifier")
        require_aware_datetime(requested_at, "requested_at")
        if type(payout_due_date) is not date:
            raise TypeError("Payout due date must be a calendar date.")
        if exit_id in self._exits:
            raise ValueError(f"Exit {exit_id!r} is already recorded.")

        effect = governance.approved_member_exit(proposal_id)
        if not isinstance(effect, MemberExitEffect):
            raise TypeError("Governance returned an invalid member-exit decision.")
        version = rules.version_for_cycle(effect.request_cycle)
        if version.rule.legal_form is LegalForm.COOPERATIVE and (
            effect.exit_type is MemberExitType.EXPULSION
            and version.rule.exit_fees.expulsion > version.rule.exit_fees.voluntary
        ):
            raise ValueError(
                "Cooperative expulsion fee cannot exceed the voluntary-exit fee."
            )
        fee = {
            MemberExitType.VOLUNTARY: version.rule.exit_fees.voluntary,
            MemberExitType.EXPULSION: version.rule.exit_fees.expulsion,
            MemberExitType.DEATH: Decimal("0"),
        }[effect.exit_type]
        max_default_date = _add_months(effect.exit_date, 12)
        max_absolute_date = _add_months(effect.exit_date, 24)
        if not effect.exit_date <= payout_due_date <= max_absolute_date:
            raise ValueError("Payout due date must be within 24 months of exit.")
        if payout_due_date > max_default_date:
            if deferral_proposal_id is None:
                raise ValueError(
                    "Payout beyond 12 months requires an approved reasoned deferral."
                )
            deferral = governance.approved_payout_deferral(deferral_proposal_id)
            if deferral.exit_proposal_id != proposal_id:
                raise ValueError("Deferral decision does not match this exit.")
            deferral.validate_exit_date(effect.exit_date)
            if deferral.extended_date != payout_due_date:
                raise ValueError("Payout due date must match the approved deferral.")
        elif deferral_proposal_id is not None:
            raise ValueError("A deferral decision is only valid beyond 12 months.")
        self._allocations.record_member_exit(
            effect.member_id, effect.exit_date, exit_id
        )
        exit_record = HybridExit(
            exit_id=exit_id,
            proposal_id=proposal_id,
            member_id=effect.member_id,
            exit_type=effect.exit_type,
            exit_date=effect.exit_date,
            request_cycle=effect.request_cycle,
            rule_version=version.version,
            currency=CurrencyCode(version.rule.currency),
            fee_percent=fee,
            payout_due_date=payout_due_date,
            requested_at=requested_at,
            status=ExitStatus.PENDING_VALUATION,
        )
        self._exits[exit_id] = exit_record
        self._audit_event(
            "hybrid_member_exit_recorded",
            exit_id,
            requested_at,
            proposal_id,
            {
                "member_id": effect.member_id,
                "exit_type": effect.exit_type.value,
                "exit_date": effect.exit_date.isoformat(),
                "request_cycle": effect.request_cycle,
                "rule_version": version.version,
                "fee_percent": str(fee),
                "payout_due_date": payout_due_date.isoformat(),
            },
        )
        return exit_record

    def resolve_valuation(
        self,
        exit_id: str,
        *,
        valuations: Iterable[HybridUnitValuation],
        contribution_cycles: Iterable[ContributionCycle],
        payouts: Iterable[ClassicPayout],
        occurred_at: datetime,
    ) -> HybridExit:
        """Resolve forward pricing and calculate the entitlement from recorded history.

        A missing eligible valuation leaves the exit pending. Contributions and
        payouts are supplied as the existing recorded source events.
        """
        exit_record = self._exit(exit_id)
        require_aware_datetime(occurred_at, "occurred_at")
        if exit_record.status is not ExitStatus.PENDING_VALUATION:
            raise ValueError("Only exits pending valuation can be resolved.")
        valuation = first_eligible_valuation(
            valuations,
            exit_record.exit_date,
            occurred_at.date(),
            exit_record.currency,
        )
        if valuation is None:
            return exit_record
        self._validate_member_arrears_currency(
            exit_record.member_id, valuation.currency
        )
        units = self._units.balance_for(exit_record.member_id)
        gross = _currency_amount(
            _multiply(units, valuation.unit_price), valuation.currency
        )
        with localcontext() as context:
            context.prec = max(
                28,
                len(gross.as_tuple().digits)
                + len(exit_record.fee_percent.as_tuple().digits)
                + 12,
            )
            fee_amount = gross * exit_record.fee_percent / Decimal("100")
        fee = _currency_amount(fee_amount, valuation.currency)
        penalties, rotation, fund = self._arrears_totals(exit_record.member_id)
        excess_pot = excess_pot_received(
            exit_record.member_id,
            exit_record.exit_date,
            valuation.currency,
            contribution_cycles,
            payouts,
        )
        net = _net_amount(gross, fee, penalties, rotation, fund, excess_pot)
        settlement = ExitSettlement(
            valuation_id=valuation.valuation_id,
            valuation_date=valuation.effective_date,
            units_redeemed=units,
            gross_unit_value=gross,
            exit_fee=fee,
            unpaid_penalties=penalties,
            unpaid_rotation_dues=rotation,
            unpaid_fund_dues=fund,
            excess_pot_received=excess_pot,
            net_amount=net,
            currency=valuation.currency,
        )

        # Validate every input before emitting the offset and redemption events.
        offset_amount = min(
            max(_net_amount(gross, fee), Decimal("0")),
            _sum_amounts(penalties, rotation, fund),
        )
        self._arrears.apply_exit_setoff(
            exit_record.member_id,
            exit_id,
            available_amount=offset_amount,
            occurred_at=occurred_at,
        )
        self._units.redeem(
            exit_record.member_id, units, f"hybrid-exit:{exit_id}:redeem"
        )
        status = (
            ExitStatus.AMOUNT_OWED
            if net < 0
            else ExitStatus.NO_PAYOUT
            if net == 0
            else ExitStatus.HELD_FOR_ESTATE
            if exit_record.exit_type is MemberExitType.DEATH and net > 0
            else ExitStatus.QUEUED
        )
        resolved = replace(exit_record, status=status, settlement=settlement)
        self._exits[exit_id] = resolved
        self._audit_event(
            "hybrid_exit_settled",
            exit_id,
            occurred_at,
            exit_record.proposal_id,
            {
                "valuation_id": valuation.valuation_id,
                "gross_unit_value": str(gross),
                "exit_fee": str(fee),
                "exit_fee_destination": settlement.exit_fee_destination,
                "penalties": str(penalties),
                "rotation_dues": str(rotation),
                "fund_dues": str(fund),
                "excess_pot_received": str(excess_pot),
                "net_amount": str(net),
                "status": status.value,
            },
        )
        return resolved

    def record_estate_proof(
        self, exit_id: str, reference: str, *, occurred_at: datetime
    ) -> HybridExit:
        """Record succession evidence and release a positive death entitlement."""
        exit_record = self._exit(exit_id)
        _identifier(reference, "Estate proof reference")
        require_aware_datetime(occurred_at, "occurred_at")
        if exit_record.exit_type is not MemberExitType.DEATH:
            raise ValueError("Estate proof applies only to death exits.")
        if exit_record.status is not ExitStatus.HELD_FOR_ESTATE:
            raise ValueError("Exit is not holding an estate entitlement.")
        updated = replace(
            exit_record,
            estate_proof_reference=reference,
            status=ExitStatus.QUEUED,
        )
        self._exits[exit_id] = updated
        self._audit_event(
            "hybrid_exit_estate_proof_recorded",
            exit_id,
            occurred_at,
            reference,
            {"member_id": exit_record.member_id},
        )
        return updated

    def consign(
        self, exit_id: str, reference: str, *, occurred_at: datetime
    ) -> HybridExit:
        """Record a deposit or sequestration reference for a disputed claim."""
        exit_record = self._exit(exit_id)
        _identifier(reference, "Consignment or sequestration reference")
        require_aware_datetime(occurred_at, "occurred_at")
        if exit_record.status not in {
            ExitStatus.HELD_FOR_ESTATE,
            ExitStatus.QUEUED,
            ExitStatus.PAYABLE,
        }:
            raise ValueError("Only an unpaid positive entitlement can be consigned.")
        updated = replace(
            exit_record,
            status=ExitStatus.CONSIGNED,
            consignment_reference=reference,
        )
        self._exits[exit_id] = updated
        self._audit_event(
            "hybrid_exit_consigned",
            exit_id,
            occurred_at,
            reference,
            {"member_id": exit_record.member_id},
        )
        return updated

    def record_external_payment(
        self, exit_id: str, reference: str, *, occurred_at: datetime
    ) -> HybridExit:
        """Record an externally executed payment without initiating a transfer."""
        exit_record = self._exit(exit_id)
        _identifier(reference, "External payment reference")
        require_aware_datetime(occurred_at, "occurred_at")
        if exit_record.status is not ExitStatus.PAYABLE:
            raise ValueError(
                "Only a payable entitlement can be marked externally paid."
            )
        if occurred_at.date() < exit_record.payout_due_date:
            raise ValueError("External payment cannot predate the payout due date.")
        updated = replace(
            exit_record,
            status=ExitStatus.PAID_EXTERNALLY,
            external_payment_reference=reference,
        )
        self._exits[exit_id] = updated
        self._audit_event(
            "hybrid_exit_external_payment_recorded",
            exit_id,
            occurred_at,
            reference,
            {"member_id": exit_record.member_id},
        )
        return updated

    def build_queue(
        self,
        report_id: str,
        *,
        currency: CurrencyCode | str,
        liquidity_cap: Decimal,
        created_at: datetime,
    ) -> ExitQueueReport:
        """Assign due positive entitlements FIFO within a currency liquidity cap."""
        _identifier(report_id, "Queue report identifier")
        require_aware_datetime(created_at, "created_at")
        normalized_currency = CurrencyCode(str(currency))
        cap = _currency_amount(liquidity_cap, normalized_currency)
        if cap < 0:
            raise ValueError("Liquidity cap must be non-negative.")
        if report_id in self._reports:
            raise ValueError(f"Queue report {report_id!r} is already recorded.")
        candidates = sorted(
            (
                item
                for item in self._exits.values()
                if item.status in {ExitStatus.QUEUED, ExitStatus.PAYABLE}
                and item.settlement is not None
                and item.settlement.net_amount > 0
                and item.settlement.currency == normalized_currency
                and item.payout_due_date <= created_at.date()
            ),
            key=lambda item: (item.exit_date, item.requested_at, item.exit_id),
        )
        remaining = cap
        liquidity_exhausted = False
        entries: list[ExitQueueEntry] = []
        for position, item in enumerate(candidates, 1):
            assert item.settlement is not None
            payable = (
                not liquidity_exhausted and item.settlement.net_amount <= remaining
            )
            status = ExitStatus.PAYABLE if payable else ExitStatus.QUEUED
            amount = item.settlement.net_amount
            if payable:
                remaining -= amount
            else:
                liquidity_exhausted = True
            entries.append(
                ExitQueueEntry(item.exit_id, item.member_id, position, amount, status)
            )
            self._exits[item.exit_id] = replace(
                item, status=status, queue_position=position
            )
        report = ExitQueueReport(
            report_id=report_id,
            currency=normalized_currency,
            liquidity_cap=cap,
            entries=tuple(entries),
            created_at=created_at,
        )
        self._reports[report_id] = report
        self._audit_event(
            "hybrid_exit_queue_reported",
            report_id,
            created_at,
            None,
            {
                "currency": str(normalized_currency),
                "liquidity_cap": str(cap),
                "entry_count": len(entries),
            },
        )
        return report

    def exit_for(self, exit_id: str) -> HybridExit:
        """Return an exit by its stable identifier."""
        return self._exit(exit_id)

    def exits(self) -> tuple[HybridExit, ...]:
        """Return exits in recording order."""
        return tuple(self._exits.values())

    def queue_reports(self) -> tuple[ExitQueueReport, ...]:
        """Return recorded liquidity queue reports in insertion order."""
        return tuple(self._reports.values())

    def audit_events(self, exit_id: str) -> tuple[AuditEvent, ...]:
        """Return audit history for an exit or queue report."""
        return self._audit.events_for("hybrid_exit", exit_id)

    def _exit(self, exit_id: str) -> HybridExit:
        try:
            return self._exits[exit_id]
        except KeyError as exc:
            raise MissingRecordError(f"No exit {exit_id!r} is recorded.") from exc

    def _arrears_currency(self, member_id: str) -> CurrencyCode | None:
        records = tuple(
            item for item in self._arrears.records() if item.member_id == member_id
        )
        currencies = {item.currency for item in records}
        if len(currencies) > 1:
            raise ValueError("Member arrears must use one currency for settlement.")
        return next(iter(currencies), None)

    def _validate_member_arrears_currency(
        self, member_id: str, currency: CurrencyCode
    ) -> None:
        arrears_currency = self._arrears_currency(member_id)
        if arrears_currency is not None and arrears_currency != currency:
            raise ValueError("Exit valuation currency must match member arrears.")

    def _arrears_totals(self, member_id: str) -> tuple[Decimal, Decimal, Decimal]:
        penalties: list[Decimal] = []
        rotation: list[Decimal] = []
        fund: list[Decimal] = []
        for record in self._arrears.records():
            if record.member_id != member_id:
                continue
            balance = self._arrears.balance_for(record.arrears_id)
            penalties.append(balance.penalty_amount)
            rotation.append(balance.rotation_amount)
            fund.append(balance.fund_amount)
        return (
            _sum_amounts(*penalties),
            _sum_amounts(*rotation),
            _sum_amounts(*fund),
        )

    def _audit_event(
        self,
        event_type: str,
        aggregate_id: str,
        occurred_at: datetime,
        source_event: str | None,
        details: Mapping[str, object],
    ) -> None:
        event_id = f"hybrid-exit:{event_type}:{aggregate_id}"
        event = self._audit.record(
            event_id,
            event_type,
            "hybrid_exit",
            aggregate_id,
            occurred_at,
            None,
            source_event,
            details,
        )
        self._audit_event_ids.add(event.event_id)


__all__ = [
    "ExitGovernanceLookup",
    "ExitQueueEntry",
    "ExitQueueReport",
    "ExitSettlement",
    "ExitStatus",
    "HybridExit",
    "HybridExitRegistry",
]
