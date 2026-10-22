from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from tontine.audit import AuditEventRegistry
from tontine.classic import ClassicRotation
from tontine.contributions import ContributionCycle, PenaltyDestination
from tontine.governance import GovernanceRegistry
from tontine.hybrid import (
    AllocationReversal,
    CatchUpChoice,
    CatchUpPolicy,
    ContributionPaymentOrder,
    HybridAllocation,
    HybridAllocationRegistry,
    HybridAllocationSnapshot,
    HybridArrearsRegistry,
    HybridArrearsSnapshot,
    HybridRule,
    HybridRuleVersion,
    HybridUnitValuation,
    PenaltyPaymentOrder,
    PendingHybridAllocation,
)
from tontine.investments import MemberUnitLedger


def rule_version() -> HybridRuleVersion:
    return HybridRuleVersion(
        1,
        1,
        0,
        HybridRule("XAF", 3000, Decimal("1000"), 30),
    )


def cycle_with_receipt() -> ContributionCycle:
    cycle = ContributionCycle(
        cycle_id="cycle-1",
        start_date=date(2027, 1, 1),
        due_date=date(2027, 1, 15),
        timezone="UTC",
    )
    cycle.add_expected_contribution("member-1", Decimal("10000"))
    cycle.record_contribution(
        "member-1",
        Decimal("10000"),
        payment_date=datetime(2027, 1, 15, 12, tzinfo=UTC),
    )
    return cycle


def record_allocation(
    registry: HybridAllocationRegistry,
    unit_ledger: MemberUnitLedger,
    *,
    valuations: tuple[HybridUnitValuation, ...] = (),
) -> HybridAllocation | PendingHybridAllocation:
    return registry.allocate(
        allocation_id="allocation-1",
        contribution_id="contribution-1",
        cycle=cycle_with_receipt(),
        member_id="member-1",
        cycle_number=1,
        rule_version=rule_version(),
        valuations=valuations,
        unit_ledger=unit_ledger,
    )


def arrears_rule_version(
    *,
    contribution_order: ContributionPaymentOrder = ContributionPaymentOrder.POT_FIRST,
) -> HybridRuleVersion:
    return HybridRuleVersion(
        1,
        1,
        0,
        HybridRule(
            "XAF",
            3000,
            Decimal("1000"),
            30,
            penalty_order=PenaltyPaymentOrder.PENALTY_FIRST,
            contribution_order=contribution_order,
            catch_up=CatchUpPolicy(deadline_cycles=1),
        ),
    )


def missed_cycle(cycle_id: str = "arrears-cycle-1") -> ContributionCycle:
    cycle = ContributionCycle(
        cycle_id=cycle_id,
        start_date=date(2027, 1, 1),
        due_date=date(2027, 1, 15),
        timezone="UTC",
        penalty_destination=PenaltyDestination.ROTATION_POT,
    )
    cycle.add_expected_contribution("member-1", Decimal("1000"))
    return cycle


def close_missed_cycle(
    registry: HybridArrearsRegistry,
    *,
    cycle_id: str = "arrears-cycle-1",
) -> str:
    records = registry.close_cycle(
        missed_cycle(cycle_id),
        cycle_number=1,
        rule_version=arrears_rule_version(),
        closed_at=datetime(2027, 1, 18, 12, tzinfo=UTC),
    )
    assert len(records) == 1
    return records[0].arrears_id


def test_allocation_snapshot_restores_records_reversals_freezes_and_audit() -> None:
    audit = AuditEventRegistry()
    registry = HybridAllocationRegistry(audit)
    unit_ledger = MemberUnitLedger()
    allocation = record_allocation(registry, unit_ledger)
    assert isinstance(allocation, HybridAllocation)
    registry.reverse(
        allocation.allocation_id,
        reversal_id="reversal-1",
        reason="Correction",
        recorded_at=datetime(2027, 1, 20, tzinfo=UTC),
        unit_ledger=unit_ledger,
    )
    registry.record_member_exit("member-2", date(2027, 2, 1), "exit-2")

    snapshot = registry.snapshot()
    restored_units = MemberUnitLedger.from_snapshot(unit_ledger.snapshot())
    restored = snapshot.restore(restored_units)

    assert restored.snapshot() == snapshot
    assert restored.audit_events(allocation.allocation_id) == registry.audit_events(
        allocation.allocation_id
    )
    with pytest.raises(ValueError, match="on or after the exit date"):
        restored.record_member_exit("member-1", date(2027, 1, 15), "exit-1")


def test_pending_allocation_snapshot_preserves_rule_and_can_resolve() -> None:
    registry = HybridAllocationRegistry()
    unit_ledger = MemberUnitLedger()
    unit_ledger.issue_units("member-2", Decimal("1"), "seed")
    pending = record_allocation(registry, unit_ledger)
    assert isinstance(pending, PendingHybridAllocation)

    snapshot = registry.snapshot()
    restored_units = MemberUnitLedger.from_snapshot(unit_ledger.snapshot())
    restored = HybridAllocationRegistry.from_snapshot(
        snapshot,
        unit_ledger=restored_units,
    )
    result = restored.resolve_pending(
        "contribution-1",
        allocated_on=date(2027, 1, 20),
        valuations=(
            HybridUnitValuation(
                "valuation-1",
                date(2027, 1, 20),
                Decimal("1000"),
                "XAF",
            ),
        ),
        unit_ledger=restored_units,
    )

    assert isinstance(result, HybridAllocation)
    assert result.units_issued == Decimal("3.0000")
    assert restored.snapshot().pending_allocations == ()
    assert restored_units.balance_for("member-1") == Decimal("3.0000")
    assert len(restored.audit_events("allocation-1")) == 2


def test_allocation_snapshot_rejects_invalid_schema_and_record_references() -> None:
    registry = HybridAllocationRegistry()
    unit_ledger = MemberUnitLedger()
    allocation = record_allocation(registry, unit_ledger)
    assert isinstance(allocation, HybridAllocation)
    snapshot = registry.snapshot()

    with pytest.raises(ValueError, match="Unsupported"):
        replace(snapshot, schema_version=2)
    with pytest.raises(ValueError, match="Allocation identifiers"):
        replace(snapshot, allocations=(allocation, allocation))

    incorrect_reversal = AllocationReversal(
        reversal_id="reversal-1",
        original_allocation_id=allocation.allocation_id,
        contribution_id=allocation.contribution_id,
        member_id=allocation.member_id,
        reason="Correction",
        recorded_at=datetime(2027, 1, 20, tzinfo=UTC),
        currency=allocation.currency,
        unit_price=allocation.unit_price,
        pot_offset=Decimal("-1"),
        fund_offset=-allocation.fund_amount,
        units_offset=-allocation.units_issued,
        cash_residual_offset=-allocation.cash_residual,
    )
    with pytest.raises(ValueError, match="exactly offset"):
        replace(snapshot, reversals=(incorrect_reversal,))


def test_allocation_snapshot_restore_requires_matching_unit_event_history() -> None:
    registry = HybridAllocationRegistry()
    unit_ledger = MemberUnitLedger()
    allocation = record_allocation(registry, unit_ledger)
    assert isinstance(allocation, HybridAllocation)

    with pytest.raises(ValueError, match="issue event is missing"):
        registry.snapshot().restore(MemberUnitLedger())


def test_pending_snapshot_requires_matching_rule_version() -> None:
    registry = HybridAllocationRegistry()
    unit_ledger = MemberUnitLedger()
    unit_ledger.issue_units("member-2", Decimal("1"), "seed")
    pending = record_allocation(registry, unit_ledger)
    assert isinstance(pending, PendingHybridAllocation)

    with pytest.raises(ValueError, match="exactly one rule version"):
        replace(registry.snapshot(), pending_versions=())


def test_snapshot_type_is_publicly_constructible() -> None:
    snapshot = HybridAllocationSnapshot(
        schema_version=1,
        allocations=(),
        pending_allocations=(),
        pending_versions=(),
        reversals=(),
        member_exit_dates=(),
        audit_events=(),
    )

    assert snapshot.restore(MemberUnitLedger()).snapshot() == snapshot


def test_arrears_snapshot_restores_histories_and_accepts_future_offsets() -> None:
    arrears = HybridArrearsRegistry()
    allocations = HybridAllocationRegistry()
    units = MemberUnitLedger()
    arrears_id = close_missed_cycle(arrears)
    units.issue_units("member-1", Decimal("1"), "seed-unit-event")
    arrears.record_catch_up_election(
        arrears_id,
        election_id="election-1",
        choice=CatchUpChoice.CATCH_UP,
        cycle_number=1,
        elected_at=datetime(2027, 1, 18, 13, tzinfo=UTC),
    )
    arrears.record_payment_application(
        arrears_id,
        payment_id="fund-payment",
        received_amount=Decimal("500"),
        payment_date=date(2027, 1, 20),
        payment_cycle_id="payment-cycle-2",
        payment_cycle_number=2,
        rule_version=arrears_rule_version(
            contribution_order=ContributionPaymentOrder.PRO_RATA
        ),
        valuations=(
            HybridUnitValuation(
                "fund-valuation",
                date(2027, 1, 20),
                Decimal("100"),
                "XAF",
            ),
        ),
        allocation_registry=allocations,
        unit_ledger=units,
        recorded_at=datetime(2027, 1, 20, 12, tzinfo=UTC),
    )
    arrears.offset_rotation_arrears(
        arrears_id,
        offset_id="offset-1",
        units=Decimal("1"),
        unit_price=Decimal("100"),
        valuation_reference="offset-valuation",
        occurred_at=datetime(2027, 1, 21, tzinfo=UTC),
        unit_ledger=units,
    )
    arrears.apply_exit_setoff(
        "member-1",
        "exit-1",
        available_amount=Decimal("20"),
        occurred_at=datetime(2027, 1, 22, tzinfo=UTC),
    )

    snapshot = arrears.snapshot()
    allocation_snapshot = allocations.snapshot()
    restored_units = MemberUnitLedger.from_snapshot(units.snapshot())
    restored_allocations = allocation_snapshot.restore(restored_units)
    restored = snapshot.restore(
        allocation_registry=restored_allocations,
        unit_ledger=restored_units,
    )

    assert restored.snapshot() == snapshot
    assert restored.balance_for(arrears_id) == arrears.balance_for(arrears_id)
    assert restored.audit_events(arrears_id) == arrears.audit_events(arrears_id)
    assert restored.cycle_audit_events("arrears-cycle-1") == (
        arrears.cycle_audit_events("arrears-cycle-1")
    )
    restored.offset_rotation_arrears(
        arrears_id,
        offset_id="offset-after-restore",
        units=Decimal("0.5"),
        unit_price=Decimal("100"),
        valuation_reference="later-valuation",
        occurred_at=datetime(2027, 1, 23, tzinfo=UTC),
        unit_ledger=restored_units,
    )
    assert restored.balance_for(arrears_id).rotation_amount == Decimal("180")
    restored.record_payment_application(
        arrears_id,
        payment_id="payment-after-restore",
        received_amount=Decimal("30"),
        payment_date=date(2027, 1, 24),
        payment_cycle_id="payment-cycle-2",
        payment_cycle_number=2,
        rule_version=arrears_rule_version(
            contribution_order=ContributionPaymentOrder.PRO_RATA
        ),
        valuations=(
            HybridUnitValuation(
                "later-fund-valuation",
                date(2027, 1, 24),
                Decimal("100"),
                "XAF",
            ),
        ),
        allocation_registry=restored_allocations,
        unit_ledger=restored_units,
        recorded_at=datetime(2027, 1, 24, 12, tzinfo=UTC),
    )
    assert len(restored.payments()) == 2


def test_restored_arrears_can_record_a_catch_up_election() -> None:
    arrears = HybridArrearsRegistry()
    arrears_id = close_missed_cycle(arrears)
    restored = arrears.snapshot().restore(
        allocation_registry=HybridAllocationRegistry(),
        unit_ledger=MemberUnitLedger(),
    )

    election = restored.record_catch_up_election(
        arrears_id,
        election_id="election-after-restore",
        choice=CatchUpChoice.CATCH_UP,
        cycle_number=1,
        elected_at=datetime(2027, 1, 18, 13, tzinfo=UTC),
    )

    assert restored.elections() == (election,)
    assert election.choice is CatchUpChoice.CATCH_UP


def test_arrears_snapshot_rejects_invalid_schema_references_and_overpayment() -> None:
    arrears = HybridArrearsRegistry()
    arrears_id = close_missed_cycle(arrears)
    arrears.record_catch_up_election(
        arrears_id,
        election_id="election-1",
        choice=CatchUpChoice.CATCH_UP,
        cycle_number=1,
        elected_at=datetime(2027, 1, 18, 13, tzinfo=UTC),
    )
    allocations = HybridAllocationRegistry()
    units = MemberUnitLedger()
    application = arrears.record_payment_application(
        arrears_id,
        payment_id="payment-1",
        received_amount=Decimal("500"),
        payment_date=date(2027, 1, 20),
        payment_cycle_id="payment-cycle-2",
        payment_cycle_number=2,
        rule_version=arrears_rule_version(
            contribution_order=ContributionPaymentOrder.PRO_RATA
        ),
        valuations=(),
        allocation_registry=allocations,
        unit_ledger=units,
        recorded_at=datetime(2027, 1, 20, 12, tzinfo=UTC),
    )
    snapshot = arrears.snapshot()

    with pytest.raises(ValueError, match="Unsupported"):
        replace(snapshot, schema_version=2)
    with pytest.raises(ValueError, match="references invalid"):
        replace(snapshot, payments=(replace(application, arrears_id="missing"),))
    excess_application = replace(
        application,
        payment_id="payment-2",
        received_amount=Decimal("1001"),
        rotation_paid=Decimal("701"),
        fund_paid=Decimal("300"),
        fund_allocation_id="payment-2",
    )
    with pytest.raises(ValueError, match="over-applies"):
        replace(snapshot, payments=(application, excess_application))
    with pytest.raises(ValueError, match="does not match its closed cycle"):
        replace(snapshot, closed_cycles=())


def test_arrears_snapshot_restore_rejects_mismatched_unit_offsets() -> None:
    arrears = HybridArrearsRegistry()
    allocations = HybridAllocationRegistry()
    units = MemberUnitLedger()
    arrears_id = close_missed_cycle(arrears)
    units.issue_units("member-1", Decimal("1"), "seed-unit-event")
    arrears.offset_rotation_arrears(
        arrears_id,
        offset_id="offset-1",
        units=Decimal("0.5"),
        unit_price=Decimal("100"),
        valuation_reference="offset-valuation",
        occurred_at=datetime(2027, 1, 19, tzinfo=UTC),
        unit_ledger=units,
    )

    with pytest.raises(ValueError, match="does not match its redemption event"):
        arrears.snapshot().restore(
            allocation_registry=allocations,
            unit_ledger=MemberUnitLedger(),
        )


def test_arrears_snapshot_is_publicly_exported() -> None:
    assert (
        HybridArrearsSnapshot(
            schema_version=1,
            records=(),
            payments=(),
            elections=(),
            forfeitures=(),
            waivers=(),
            offsets=(),
            exit_offsets=(),
            closed_cycles=(),
            settled_exit_ids=(),
            audit_events=(),
        ).records
        == ()
    )


def test_arrears_snapshot_preserves_forfeitures_and_penalty_waivers() -> None:
    arrears = HybridArrearsRegistry()
    disabled = missed_cycle("disabled-cycle")
    arrears.close_cycle(
        disabled,
        cycle_number=1,
        rule_version=HybridRuleVersion(
            1,
            1,
            0,
            HybridRule(
                "XAF",
                3000,
                Decimal("1000"),
                30,
                catch_up=CatchUpPolicy(allowed=False),
            ),
        ),
        closed_at=datetime(2027, 1, 18, 12, tzinfo=UTC),
    )
    cycle = ContributionCycle(
        cycle_id="penalty-cycle",
        start_date=date(2027, 2, 1),
        due_date=date(2027, 2, 15),
        timezone="UTC",
        grace_period_days=2,
        late_penalty=Decimal("50"),
        penalty_currency="XAF",
        penalty_destination=PenaltyDestination.ROTATION_POT,
    )
    cycle.add_expected_contribution("member-1", Decimal("1000"))
    records = arrears.close_cycle(
        cycle,
        cycle_number=2,
        rule_version=arrears_rule_version(),
        closed_at=datetime(2027, 2, 18, 12, tzinfo=UTC),
    )
    governance = GovernanceRegistry(
        ("member-1", "member-2", "member-3", "member-4"),
        ClassicRotation.from_active_members(
            ("member-1", "member-2", "member-3", "member-4")
        ),
    )
    assessment_id = cycle.recorded_contributions[
        "member-1"
    ].penalty_record.assessment_id
    proposal = governance.create_penalty_waiver_proposal(
        proposal_id="waiver-decision",
        title="Waive penalty",
        description="Approve a penalty waiver.",
        proposer_id="member-2",
        penalty_assessment_id=assessment_id,
        member_id="member-1",
        current_cycle=3,
        approval_threshold=Decimal("60"),
        created_at=datetime(2027, 2, 19, tzinfo=UTC),
        voting_deadline=datetime(2027, 2, 28, tzinfo=UTC),
    )
    governance.open_proposal(
        proposal.proposal_id,
        occurred_at=datetime(2027, 2, 20, tzinfo=UTC),
    )
    for member_id in proposal.eligible_member_ids:
        governance.vote(
            proposal.proposal_id,
            member_id,
            "yes",
            occurred_at=datetime(2027, 2, 21, tzinfo=UTC),
        )
    governance.evaluate(
        proposal.proposal_id,
        occurred_at=datetime(2027, 2, 28, tzinfo=UTC),
    )
    arrears.waive_penalty(
        records[0].arrears_id,
        waiver_id="waiver-event",
        proposal_id="waiver-decision",
        governance=governance,
        occurred_at=datetime(2027, 3, 1, tzinfo=UTC),
    )

    restored = arrears.snapshot().restore(
        allocation_registry=HybridAllocationRegistry(),
        unit_ledger=MemberUnitLedger(),
    )

    assert restored.snapshot() == arrears.snapshot()
    assert restored.forfeitures() == arrears.forfeitures()
    assert restored.waivers() == arrears.waivers()
    assert restored.balance_for(records[0].arrears_id).penalty_amount == 0
