from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from tontine.classic import ClassicRotation
from tontine.contributions import (
    ContributionCycle,
    CycleStatus,
    PenaltyDestination,
)
from tontine.exceptions import MissingRecordError
from tontine.governance import GovernanceRegistry
from tontine.hybrid import (
    CatchUpChoice,
    CatchUpPolicy,
    ContributionPaymentOrder,
    ForfeitureCause,
    HybridAllocation,
    HybridAllocationRegistry,
    HybridArrearsRegistry,
    HybridRule,
    HybridRuleVersion,
    HybridUnitValuation,
    PenaltyPaymentOrder,
    PendingAllocationReason,
    PendingHybridAllocation,
)
from tontine.investments import MemberUnitLedger


def rule_version(
    *,
    penalty_order: PenaltyPaymentOrder = PenaltyPaymentOrder.PENALTY_FIRST,
    contribution_order: ContributionPaymentOrder = ContributionPaymentOrder.POT_FIRST,
    catch_up: CatchUpPolicy | None = None,
    currency: str = "XAF",
) -> HybridRuleVersion:
    rule = HybridRule(
        currency=currency,
        fund_share_bps=3000,
        launch_unit_price=Decimal("100"),
        max_valuation_age_days=30,
        penalty_order=penalty_order,
        contribution_order=contribution_order,
        catch_up=catch_up or CatchUpPolicy(),
    )
    return HybridRuleVersion(1, 1, 0, rule)


def missed_cycle(
    *,
    expected: str = "1000",
    penalty: str = "0",
    cycle_id: str = "cycle-1",
) -> ContributionCycle:
    cycle = ContributionCycle(
        cycle_id=cycle_id,
        start_date=date(2027, 1, 1),
        due_date=date(2027, 1, 15),
        timezone="UTC",
        grace_period_days=2,
        late_penalty=Decimal(penalty),
        penalty_currency="XAF" if penalty != "0" else None,
        penalty_destination=PenaltyDestination.ROTATION_POT,
    )
    cycle.add_expected_contribution("member-1", Decimal(expected))
    return cycle


def paid_cycle(cycle_id: str = "cycle-2") -> ContributionCycle:
    cycle = ContributionCycle(
        cycle_id=cycle_id,
        start_date=date(2027, 2, 1),
        due_date=date(2027, 2, 15),
        timezone="UTC",
    )
    cycle.add_expected_contribution("member-1", Decimal("1000"))
    cycle.record_contribution(
        "member-1",
        Decimal("1000"),
        payment_date=datetime(2027, 2, 15, 12, tzinfo=UTC),
    )
    return cycle


def close_missed(
    registry: HybridArrearsRegistry,
    *,
    cycle: ContributionCycle | None = None,
    version: HybridRuleVersion | None = None,
) -> str:
    created = registry.close_cycle(
        cycle or missed_cycle(penalty="50"),
        cycle_number=1,
        rule_version=version or rule_version(),
        closed_at=datetime(2027, 1, 18, 12, tzinfo=UTC),
    )
    assert len(created) == 1
    return created[0].arrears_id


def test_cycle_close_records_missed_contribution_without_issuing_units() -> None:
    registry = HybridArrearsRegistry()
    cycle = missed_cycle(penalty="50")
    arrears_id = close_missed(registry, cycle=cycle)

    assert cycle.status is CycleStatus.CLOSED
    assert cycle.recorded_contributions["member-1"].status.value == "missed"
    assert registry.balance_for(arrears_id).rotation_amount == Decimal("700")
    assert registry.balance_for(arrears_id).fund_amount == Decimal("300")
    assert registry.balance_for(arrears_id).penalty_amount == Decimal("50")
    assert registry.record_for(arrears_id).penalty_assessment_id == (
        cycle.recorded_contributions["member-1"].penalty_record.assessment_id
    )
    assert registry.cycle_audit_events(cycle.cycle_id)[0].event_type == (
        "hybrid_cycle_closed"
    )
    assert registry.audit_events(arrears_id)[0].event_type == ("hybrid_arrears_created")
    assert not registry.payments()
    assert not MemberUnitLedger().total_units


def test_exit_setoff_reduces_penalty_rotation_and_fund_arrears() -> None:
    registry = HybridArrearsRegistry()
    arrears_id = close_missed(registry, cycle=missed_cycle(penalty="50"))

    offsets = registry.apply_exit_setoff(
        "member-1",
        "exit-1",
        available_amount=Decimal("800"),
        occurred_at=datetime(2027, 1, 20, 12, tzinfo=UTC),
    )

    assert len(offsets) == 1
    assert offsets[0].penalty_amount == Decimal("50")
    assert offsets[0].rotation_amount == Decimal("700")
    assert offsets[0].fund_amount == Decimal("50")
    assert registry.balance_for(arrears_id).penalty_amount == 0
    assert registry.balance_for(arrears_id).rotation_amount == 0
    assert registry.balance_for(arrears_id).fund_amount == Decimal("250")


def test_fund_arrears_are_not_payable_without_a_catch_up_election() -> None:
    registry = HybridArrearsRegistry()
    arrears_id = close_missed(registry, cycle=missed_cycle())
    ledger = MemberUnitLedger()

    with pytest.raises(ValueError, match="exceeds eligible arrears"):
        registry.record_payment_application(
            arrears_id,
            payment_id="payment-1",
            received_amount=Decimal("800"),
            payment_date=date(2027, 1, 19),
            payment_cycle_id="cycle-2",
            payment_cycle_number=2,
            rule_version=rule_version(),
            valuations=(),
            allocation_registry=HybridAllocationRegistry(),
            unit_ledger=ledger,
            recorded_at=datetime(2027, 1, 19, 12, tzinfo=UTC),
        )

    assert not registry.payments()
    assert ledger.total_units == 0


def test_group_can_disable_catch_up_without_clearing_rotation_arrears() -> None:
    registry = HybridArrearsRegistry()
    arrears_id = close_missed(
        registry,
        cycle=missed_cycle(),
        version=rule_version(catch_up=CatchUpPolicy(allowed=False)),
    )

    assert registry.balance_for(arrears_id).fund_amount == 0
    assert registry.balance_for(arrears_id).rotation_amount == Decimal("700")
    assert registry.forfeitures()[0].cause is ForfeitureCause.CATCH_UP_DISABLED


@pytest.mark.parametrize(
    ("penalty_order", "received", "expected_penalty", "expected_rotation"),
    [
        (PenaltyPaymentOrder.PENALTY_FIRST, "350", "50", "300"),
        (PenaltyPaymentOrder.PENALTY_LAST, "350", "0", "350"),
        (PenaltyPaymentOrder.PRO_RATA, "350", "16", "334"),
    ],
)
def test_payment_application_uses_and_records_penalty_order(
    penalty_order: PenaltyPaymentOrder,
    received: str,
    expected_penalty: str,
    expected_rotation: str,
) -> None:
    registry = HybridArrearsRegistry()
    arrears_id = close_missed(registry)
    registry.record_catch_up_election(
        arrears_id,
        election_id="election-1",
        choice=CatchUpChoice.CATCH_UP,
        cycle_number=1,
        elected_at=datetime(2027, 1, 18, 13, tzinfo=UTC),
    )
    assert registry.audit_events(arrears_id)[-1].event_type == (
        "hybrid_catch_up_elected"
    )
    application = registry.record_payment_application(
        arrears_id,
        payment_id="payment-1",
        received_amount=Decimal(received),
        payment_date=date(2027, 1, 19),
        payment_cycle_id="cycle-2",
        payment_cycle_number=2,
        rule_version=rule_version(penalty_order=penalty_order),
        valuations=(),
        allocation_registry=HybridAllocationRegistry(),
        unit_ledger=MemberUnitLedger(),
        recorded_at=datetime(2027, 1, 19, 12, tzinfo=UTC),
    )

    assert application.penalty_paid == Decimal(expected_penalty)
    assert application.rotation_paid == Decimal(expected_rotation)
    assert application.rule_version == 1
    assert (
        application.penalty_paid + application.rotation_paid + application.fund_paid
        == (application.received_amount)
    )


@pytest.mark.parametrize(
    ("order", "expected_rotation", "expected_fund"),
    [
        (ContributionPaymentOrder.POT_FIRST, "500", "0"),
        (ContributionPaymentOrder.PRO_RATA, "350", "150"),
    ],
)
def test_partial_contribution_payment_uses_contribution_order(
    order: ContributionPaymentOrder,
    expected_rotation: str,
    expected_fund: str,
) -> None:
    registry = HybridArrearsRegistry()
    arrears_id = close_missed(registry, cycle=missed_cycle())
    registry.record_catch_up_election(
        arrears_id,
        election_id="election-1",
        choice=CatchUpChoice.CATCH_UP,
        cycle_number=1,
        elected_at=datetime(2027, 1, 18, 13, tzinfo=UTC),
    )
    application = registry.record_payment_application(
        arrears_id,
        payment_id="payment-1",
        received_amount=Decimal("500"),
        payment_date=date(2027, 1, 19),
        payment_cycle_id="cycle-2",
        payment_cycle_number=2,
        rule_version=rule_version(contribution_order=order),
        valuations=(),
        allocation_registry=HybridAllocationRegistry(),
        unit_ledger=MemberUnitLedger(),
        recorded_at=datetime(2027, 1, 19, 12, tzinfo=UTC),
    )

    assert application.rotation_paid == Decimal(expected_rotation)
    assert application.fund_paid == Decimal(expected_fund)


def test_member_catch_up_is_pending_without_valuation_and_reversible() -> None:
    arrears = HybridArrearsRegistry()
    arrears_id = close_missed(arrears, cycle=missed_cycle())
    allocation_registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    ledger.issue_units("another-member", Decimal("1"), "seed")
    arrears.record_payment_application(
        arrears_id,
        payment_id="rotation-payment",
        received_amount=Decimal("700"),
        payment_date=date(2027, 1, 19),
        payment_cycle_id="cycle-2",
        payment_cycle_number=2,
        rule_version=rule_version(),
        valuations=(),
        allocation_registry=allocation_registry,
        unit_ledger=ledger,
        recorded_at=datetime(2027, 1, 19, 12, tzinfo=UTC),
    )
    arrears.record_catch_up_election(
        arrears_id,
        election_id="election-1",
        choice=CatchUpChoice.CATCH_UP,
        cycle_number=2,
        elected_at=datetime(2027, 1, 19, 13, tzinfo=UTC),
    )
    application = arrears.record_payment_application(
        arrears_id,
        payment_id="fund-payment",
        received_amount=Decimal("300"),
        payment_date=date(2027, 1, 20),
        payment_cycle_id="cycle-2",
        payment_cycle_number=2,
        rule_version=rule_version(),
        valuations=(),
        allocation_registry=allocation_registry,
        unit_ledger=ledger,
        recorded_at=datetime(2027, 1, 20, 12, tzinfo=UTC),
    )

    pending = allocation_registry.pending_allocations()[0]
    assert isinstance(pending, PendingHybridAllocation)
    assert pending.reason is PendingAllocationReason.NO_VALUATION
    assert pending.allocation_type.value == "catch_up"
    assert pending.source_arrears_id == arrears_id
    assert ledger.balance_for("member-1") == 0

    resolved = allocation_registry.resolve_pending(
        "fund-payment",
        allocated_on=date(2027, 1, 20),
        valuations=(
            HybridUnitValuation(
                "valuation-1", date(2027, 1, 20), Decimal("100"), "XAF"
            ),
        ),
        unit_ledger=ledger,
    )
    assert isinstance(resolved, HybridAllocation)
    assert resolved.allocation_type.value == "catch_up"
    assert resolved.source_arrears_id == arrears_id
    assert application.fund_allocation_id == resolved.allocation_id
    assert ledger.balance_for("member-1") == Decimal("3.0000")

    reversal = allocation_registry.reverse(
        resolved.allocation_id,
        reversal_id="fund-payment-reversal",
        reason="Correct the recorded catch-up receipt.",
        recorded_at=datetime(2027, 1, 21, tzinfo=UTC),
        unit_ledger=ledger,
    )
    assert reversal.units_offset == Decimal("-3.0000")
    assert ledger.balance_for("member-1") == 0


def test_deadline_default_forfeits_only_fund_arrears() -> None:
    registry = HybridArrearsRegistry()
    arrears_id = close_missed(registry, cycle=missed_cycle())

    registry.close_cycle(
        paid_cycle(),
        cycle_number=2,
        rule_version=rule_version(),
        closed_at=datetime(2027, 2, 18, 12, tzinfo=UTC),
    )

    assert len(registry.forfeitures()) == 1
    assert registry.forfeitures()[0].cause is ForfeitureCause.DEFAULTED
    assert registry.balance_for(arrears_id).fund_amount == 0
    assert registry.balance_for(arrears_id).rotation_amount == Decimal("700")
    assert registry.elections()[0].is_default
    assert registry.audit_events(arrears_id)[-1].event_type == (
        "hybrid_fund_share_forfeited"
    )
    with pytest.raises(ValueError, match="Redemption is blocked"):
        registry.redeem_units(
            "member-1",
            Decimal("1"),
            "redeem-1",
            unit_ledger=MemberUnitLedger(),
        )


def test_fund_forfeit_does_not_clear_rotation_arrears_and_blocks_catch_up() -> None:
    registry = HybridArrearsRegistry()
    arrears_id = close_missed(registry, cycle=missed_cycle())
    registry.record_catch_up_election(
        arrears_id,
        election_id="forfeit-election",
        choice=CatchUpChoice.FORFEIT,
        cycle_number=1,
        elected_at=datetime(2027, 1, 18, 13, tzinfo=UTC),
    )

    assert registry.balance_for(arrears_id).fund_amount == 0
    assert registry.balance_for(arrears_id).rotation_amount == Decimal("700")
    with pytest.raises(ValueError, match="No unpaid fund share remains"):
        registry.record_catch_up_election(
            arrears_id,
            election_id="second-election",
            choice=CatchUpChoice.CATCH_UP,
            cycle_number=1,
            elected_at=datetime(2027, 1, 18, 14, tzinfo=UTC),
        )


def test_unit_offset_reduces_rotation_arrears_and_redemption_gate() -> None:
    registry = HybridArrearsRegistry()
    arrears_id = close_missed(registry, cycle=missed_cycle())
    ledger = MemberUnitLedger()
    ledger.issue_units("member-1", Decimal("4"), "seed")
    offset = registry.offset_rotation_arrears(
        arrears_id,
        offset_id="offset-1",
        units=Decimal("2"),
        unit_price=Decimal("300"),
        valuation_reference="valuation-1",
        occurred_at=datetime(2027, 1, 19, tzinfo=UTC),
        unit_ledger=ledger,
    )

    assert offset.amount == Decimal("600")
    assert registry.balance_for(arrears_id).rotation_amount == Decimal("100")
    with pytest.raises(ValueError, match="rotation arrears remain"):
        registry.redeem_units(
            "member-1", Decimal("0.5"), "redeem-blocked", unit_ledger=ledger
        )
    registry.offset_rotation_arrears(
        arrears_id,
        offset_id="offset-2",
        units=Decimal("1"),
        unit_price=Decimal("100"),
        valuation_reference="valuation-2",
        occurred_at=datetime(2027, 1, 20, tzinfo=UTC),
        unit_ledger=ledger,
    )
    registry.redeem_units(
        "member-1", Decimal("0.5"), "redeem-allowed", unit_ledger=ledger
    )
    assert registry.balance_for(arrears_id).rotation_amount == 0
    assert ledger.balance_for("member-1") == Decimal("0.5")


def test_penalty_waiver_requires_matching_approved_governance_decision() -> None:
    registry = HybridArrearsRegistry()
    cycle = missed_cycle(penalty="50")
    arrears_id = close_missed(registry, cycle=cycle)
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
        current_cycle=2,
        approval_threshold=Decimal("60"),
        created_at=datetime(2027, 1, 19, tzinfo=UTC),
        voting_deadline=datetime(2027, 1, 30, tzinfo=UTC),
    )
    governance.open_proposal(
        proposal.proposal_id, occurred_at=datetime(2027, 1, 20, tzinfo=UTC)
    )
    for member_id in proposal.eligible_member_ids:
        governance.vote(
            proposal.proposal_id,
            member_id,
            "yes",
            occurred_at=datetime(2027, 1, 21, tzinfo=UTC),
        )
    governance.evaluate(
        proposal.proposal_id, occurred_at=datetime(2027, 1, 30, tzinfo=UTC)
    )

    waiver = registry.waive_penalty(
        arrears_id,
        waiver_id="waiver-event",
        proposal_id="waiver-decision",
        governance=governance,
        occurred_at=datetime(2027, 1, 31, tzinfo=UTC),
    )

    assert waiver.assessment_id == assessment_id
    assert waiver.amount == Decimal("50")
    assert registry.balance_for(arrears_id).penalty_amount == 0


def test_waiver_rejects_unapproved_or_mismatched_decision() -> None:
    registry = HybridArrearsRegistry()
    arrears_id = close_missed(registry, cycle=missed_cycle(penalty="50"))
    governance = GovernanceRegistry(
        ("member-1", "member-2", "member-3"),
        ClassicRotation.from_active_members(("member-1", "member-2", "member-3")),
    )

    with pytest.raises(MissingRecordError, match="was not found"):
        registry.waive_penalty(
            arrears_id,
            waiver_id="waiver-event",
            proposal_id="missing-decision",
            governance=governance,
            occurred_at=datetime(2027, 1, 20, tzinfo=UTC),
        )
