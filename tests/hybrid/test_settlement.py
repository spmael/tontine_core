from datetime import UTC, date, datetime
from decimal import Decimal

from tontine.classic import ClassicPayout, ClassicRotation
from tontine.contributions import ContributionCycle, CycleStatus
from tontine.governance import (
    GovernanceRegistry,
    MemberExitType,
    ProposalStatus,
    VoteChoice,
)
from tontine.hybrid import (
    CatchUpChoice,
    HybridAllocationRegistry,
    HybridArrearsRegistry,
    HybridExitRegistry,
    HybridRule,
    HybridRuleSchedule,
    HybridRuleVersion,
    HybridSettlementHistory,
    HybridUnitValuation,
    StatuteFlags,
    settlement_position,
)
from tontine.investments import MemberUnitLedger
from tontine.members import Member, MemberRole
from tontine.reporting import InvestmentSummary, build_member_statement

MEMBER_ID = "member-a"
RULE_VERSION = HybridRuleVersion(
    1,
    1,
    0,
    HybridRule(
        currency="XAF",
        fund_share_bps=3000,
        launch_unit_price=Decimal("100"),
        max_valuation_age_days=30,
    ),
)
RULES = HybridRuleSchedule("group-1", (RULE_VERSION,))


def test_settlement_position_reports_event_derived_hybrid_history() -> None:
    member = Member.create(
        MEMBER_ID,
        "Member A",
        MemberRole.MEMBER,
        date(2027, 1, 1),
    )
    unit_ledger = MemberUnitLedger()
    allocation_registry = HybridAllocationRegistry()
    arrears_registry = HybridArrearsRegistry()

    paid_cycle = ContributionCycle(
        "cycle-1",
        date(2027, 1, 1),
        date(2027, 1, 31),
        "UTC",
    )
    paid_cycle.add_expected_contribution(MEMBER_ID, Decimal("1000"))
    paid_cycle.record_contribution(
        MEMBER_ID,
        Decimal("1000"),
        payment_date=datetime(2027, 1, 31, 12, tzinfo=UTC),
    )
    allocation_registry.allocate(
        allocation_id="allocation-1",
        contribution_id="contribution-1",
        cycle=paid_cycle,
        member_id=MEMBER_ID,
        cycle_number=1,
        rule_version=RULE_VERSION,
        valuations=(),
        unit_ledger=unit_ledger,
    )

    missed_cycle = ContributionCycle(
        "cycle-2",
        date(2027, 2, 1),
        date(2027, 2, 15),
        "UTC",
        grace_period_days=0,
        late_penalty=Decimal("50"),
        penalty_currency="XAF",
    )
    missed_cycle.add_expected_contribution(MEMBER_ID, Decimal("1000"))
    arrears = arrears_registry.close_cycle(
        missed_cycle,
        cycle_number=2,
        rule_version=RULE_VERSION,
        closed_at=datetime(2027, 2, 16, 12, tzinfo=UTC),
    )[0]
    arrears_registry.record_catch_up_election(
        arrears.arrears_id,
        election_id="election-1",
        choice=CatchUpChoice.CATCH_UP,
        cycle_number=2,
        elected_at=datetime(2027, 2, 16, 13, tzinfo=UTC),
    )
    arrears_registry.record_payment_application(
        arrears.arrears_id,
        payment_id="payment-1",
        received_amount=Decimal("250"),
        payment_date=date(2027, 2, 17),
        payment_cycle_id="cycle-3",
        payment_cycle_number=3,
        rule_version=RULE_VERSION,
        valuations=(),
        allocation_registry=allocation_registry,
        unit_ledger=unit_ledger,
        recorded_at=datetime(2027, 2, 17, 12, tzinfo=UTC),
    )
    arrears_registry.offset_rotation_arrears(
        arrears.arrears_id,
        offset_id="rotation-offset-1",
        units=Decimal("1"),
        unit_price=Decimal("100"),
        valuation_reference="valuation-offset",
        occurred_at=datetime(2027, 2, 18, 12, tzinfo=UTC),
        unit_ledger=unit_ledger,
    )
    due_cycle = ContributionCycle(
        "cycle-3",
        date(2027, 2, 16),
        date(2027, 2, 28),
        "UTC",
        status=CycleStatus.DUE,
    )
    due_cycle.add_expected_contribution(MEMBER_ID, Decimal("100"))
    due_cycle.record_contribution(
        MEMBER_ID,
        Decimal("40"),
        payment_date=datetime(2027, 2, 20, 12, tzinfo=UTC),
    )
    allocation_registry.allocate(
        allocation_id="allocation-current",
        contribution_id="contribution-current",
        cycle=due_cycle,
        member_id=MEMBER_ID,
        cycle_number=3,
        rule_version=RULE_VERSION,
        valuations=(),
        unit_ledger=unit_ledger,
    )
    pending_cycle = ContributionCycle(
        "cycle-4",
        date(2027, 3, 1),
        date(2027, 3, 15),
        "UTC",
        status=CycleStatus.DUE,
    )
    pending_cycle.add_expected_contribution(MEMBER_ID, Decimal("100"))
    pending_cycle.record_contribution(
        MEMBER_ID,
        Decimal("100"),
        payment_date=datetime(2027, 3, 15, 12, tzinfo=UTC),
    )
    allocation_registry.allocate(
        allocation_id="allocation-pending",
        contribution_id="contribution-pending",
        cycle=pending_cycle,
        member_id=MEMBER_ID,
        cycle_number=4,
        rule_version=RULE_VERSION,
        valuations=(),
        unit_ledger=unit_ledger,
    )

    payouts = (
        ClassicPayout(
            cycle_number=1,
            recipient_id=MEMBER_ID,
            amount=Decimal("500"),
            currency="XAF",
            recorded_at=datetime(2027, 1, 31, 13, tzinfo=UTC),
            source_event="payout-1",
        ),
    )
    governance = GovernanceRegistry(
        ("member-a", "member-b", "member-c", "member-d", "member-e"),
        ClassicRotation.from_active_members(
            ("member-a", "member-b", "member-c", "member-d", "member-e")
        ),
    )
    proposal = governance.create_member_exit_proposal(
        proposal_id="exit-decision",
        title="Member exit",
        description="Approve member exit.",
        proposer_id="member-b",
        member_id=MEMBER_ID,
        exit_type=MemberExitType.VOLUNTARY,
        exit_date=date(2027, 4, 1),
        request_cycle=4,
        approval_threshold=Decimal("60"),
        created_at=datetime(2027, 3, 20, tzinfo=UTC),
        voting_deadline=datetime(2027, 3, 25, tzinfo=UTC),
    )
    governance.open_proposal(
        proposal.proposal_id,
        occurred_at=datetime(2027, 3, 21, tzinfo=UTC),
    )
    for voter in proposal.eligible_member_ids:
        governance.vote(
            proposal.proposal_id,
            voter,
            VoteChoice.YES,
            occurred_at=datetime(2027, 3, 22, tzinfo=UTC),
        )
    assert (
        governance.evaluate(
            proposal.proposal_id,
            occurred_at=datetime(2027, 3, 25, tzinfo=UTC),
        )
        is ProposalStatus.APPROVED
    )

    exit_registry = HybridExitRegistry(
        allocation_registry,
        arrears_registry,
        unit_ledger,
    )
    exit_registry.record_exit(
        exit_id="exit-1",
        proposal_id=proposal.proposal_id,
        governance=governance,
        rules=RULES,
        payout_due_date=date(2027, 4, 30),
        requested_at=datetime(2027, 3, 26, tzinfo=UTC),
    )
    pending_history = HybridSettlementHistory.from_registries(
        rule_schedule=RULES,
        allocation_registry=allocation_registry,
        arrears_registry=arrears_registry,
        exit_registry=exit_registry,
        contribution_cycles=(paid_cycle, missed_cycle, due_cycle, pending_cycle),
        payouts=payouts,
    )
    pending_position = settlement_position(pending_history, member, None)

    assert pending_position.rotation_paid_in == Decimal("1010")
    assert pending_position.rotation_received == Decimal("500")
    assert pending_position.rotation_position == Decimal("510")
    assert pending_position.unpaid_rotation_dues == Decimal("400")
    assert pending_position.unpaid_fund_dues == Decimal("300")
    assert pending_position.unpaid_penalties == Decimal("0")
    assert pending_position.open_contribution_dues == Decimal("60")
    assert pending_position.outstanding_dues == Decimal("760")
    assert pending_position.units == Decimal("2")
    assert pending_position.unit_value is None
    assert pending_position.statute_flags == RULE_VERSION.rule.statute_flags
    assert {item.allocation_id for item in pending_position.pending_allocations} == {
        "allocation-current",
        "allocation-pending",
    }
    assert pending_position.pending_exits[0].exit_id == "exit-1"
    assert pending_position.elections[0].election_id == "election-1"
    assert pending_position.rotation_offsets[0].offset_id == "rotation-offset-1"

    valuation = HybridUnitValuation(
        "valuation-exit",
        date(2027, 4, 5),
        Decimal("120"),
        "XAF",
    )
    exit_registry.resolve_valuation(
        "exit-1",
        valuations=(valuation,),
        contribution_cycles=(paid_cycle, missed_cycle, due_cycle, pending_cycle),
        payouts=payouts,
        occurred_at=datetime(2027, 4, 5, 12, tzinfo=UTC),
    )
    settled_history = HybridSettlementHistory.from_registries(
        rule_schedule=RULES,
        allocation_registry=allocation_registry,
        arrears_registry=arrears_registry,
        exit_registry=exit_registry,
        contribution_cycles=(paid_cycle, missed_cycle, due_cycle, pending_cycle),
        payouts=payouts,
    )
    position = settlement_position(settled_history, member, valuation)
    statement = build_member_statement(
        member_id=MEMBER_ID,
        display_name=member.display_name,
        base_currency="XAF",
        contributions=(),
        payouts=(),
        investment=InvestmentSummary(
            position.units,
            Decimal("0"),
            position.unit_value or Decimal("0"),
            "XAF",
        ),
        hybrid_position=position,
    )

    assert position.units == Decimal("0")
    assert position.unit_value == Decimal("0")
    assert position.unpaid_rotation_dues == Decimal("160")
    assert position.unpaid_fund_dues == Decimal("300")
    assert position.open_contribution_dues == Decimal("60")
    assert position.exit_offsets[0].exit_id == "exit-1"
    assert statement.hybrid_position is not None
    assert statement.hybrid_position.position is position
    assert statement.hybrid_position.unit_liability_flag is True
    assert statement.hybrid_position.priority_lines[0][0] == "rotation pot"
    assert statement.hybrid_position.priority_lines[1][0] == "member funds: redeemable"
    assert [line[0] for line in statement.hybrid_position.event_lines] == [
        "pending allocation",
        "pending allocation",
        "pending exit",
        "catch-up election",
        "rotation arrears offset",
        "exit arrears offset",
    ]
    assert statement.hybrid_position.position.total_owed == Decimal("520")


def test_unconditional_redemption_refusal_changes_default_unit_liability_flag() -> None:
    rule = HybridRule(
        currency="XAF",
        fund_share_bps=3000,
        launch_unit_price=Decimal("100"),
        max_valuation_age_days=30,
        statute_flags=StatuteFlags(
            unconditional_redemption_refusal=True,
            pro_rata_wind_up=True,
        ),
    )
    history = HybridSettlementHistory(
        rule_schedule=HybridRuleSchedule(
            "group-1",
            (HybridRuleVersion(1, 1, 0, rule),),
        )
    )
    member = Member.create(
        MEMBER_ID,
        "Member A",
        MemberRole.MEMBER,
        date(2027, 1, 1),
    )
    position = settlement_position(
        history,
        member,
        HybridUnitValuation(
            "valuation-1",
            date(2027, 1, 1),
            Decimal("100"),
            "XAF",
        ),
    )

    statement = build_member_statement(
        member_id=MEMBER_ID,
        display_name=member.display_name,
        base_currency="XAF",
        contributions=(),
        payouts=(),
        investment=InvestmentSummary(Decimal("0"), Decimal("0"), Decimal("0"), "XAF"),
        hybrid_position=position,
    )
    assert statement.hybrid_position is not None
    assert statement.hybrid_position.unit_liability_flag is False
    assert statement.hybrid_position.priority_lines[0][0] == "rotation pot"
    assert statement.hybrid_position.priority_lines[1][0] == "member funds: redeemable"


def test_settlement_history_snapshots_mutable_contribution_cycles() -> None:
    member = Member.create(
        MEMBER_ID,
        "Member A",
        MemberRole.MEMBER,
        date(2027, 1, 1),
    )
    cycle = ContributionCycle(
        "cycle-due",
        date(2027, 1, 1),
        date(2027, 1, 31),
        "UTC",
        status=CycleStatus.DUE,
    )
    cycle.add_expected_contribution(MEMBER_ID, Decimal("100"))
    allocation_registry = HybridAllocationRegistry()
    arrears_registry = HybridArrearsRegistry()
    exit_registry = HybridExitRegistry(
        allocation_registry,
        arrears_registry,
        MemberUnitLedger(),
    )
    history = HybridSettlementHistory.from_registries(
        rule_schedule=RULES,
        allocation_registry=allocation_registry,
        arrears_registry=arrears_registry,
        exit_registry=exit_registry,
        contribution_cycles=(cycle,),
        payouts=(),
    )

    cycle.expected_contributions[MEMBER_ID] = Decimal("10")

    position = settlement_position(history, member, None)

    assert position.open_contribution_dues == Decimal("100")
