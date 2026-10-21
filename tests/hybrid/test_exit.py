from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from tontine.classic import ClassicPayout, ClassicRotation
from tontine.contributions import ContributionCycle
from tontine.governance import (
    GovernanceRegistry,
    MemberExitType,
    ProposalStatus,
    VoteChoice,
)
from tontine.hybrid import (
    ExitFeeSchedule,
    ExitStatus,
    HybridAllocationRegistry,
    HybridArrearsRegistry,
    HybridExit,
    HybridExitRegistry,
    HybridExitSnapshot,
    HybridRule,
    HybridRuleSchedule,
    HybridRuleVersion,
    HybridUnitValuation,
    LegalForm,
)
from tontine.investments import MemberUnitLedger

EXIT_DATE = date(2027, 1, 10)
NOW = datetime(2027, 1, 20, tzinfo=UTC)


def rules(
    *,
    fees: ExitFeeSchedule | None = None,
    legal_form: LegalForm = LegalForm.UNREGISTERED,
    versions: tuple[HybridRuleVersion, ...] | None = None,
) -> HybridRuleSchedule:
    if versions is None:
        rule = HybridRule(
            currency="XAF",
            fund_share_bps=3000,
            launch_unit_price=Decimal("100"),
            max_valuation_age_days=30,
            exit_fees=fees or ExitFeeSchedule(),
            legal_form=legal_form,
        )
        versions = (HybridRuleVersion(1, 1, 0, rule),)
    return HybridRuleSchedule("group-1", versions)


def approved_exit(
    *,
    exit_type: MemberExitType = MemberExitType.VOLUNTARY,
    member_id: str = "member-a",
    approved: bool = True,
) -> tuple[GovernanceRegistry, str]:
    members = ("member-a", "member-b", "member-c", "member-d", "member-e")
    governance = GovernanceRegistry(
        members, ClassicRotation.from_active_members(members)
    )
    proposal = governance.create_member_exit_proposal(
        proposal_id="exit-decision",
        title="Member exit",
        description="Approve exit.",
        proposer_id="member-b",
        member_id=member_id,
        exit_type=exit_type,
        exit_date=EXIT_DATE,
        request_cycle=2,
        approval_threshold=Decimal("60"),
        created_at=datetime(2027, 1, 1, tzinfo=UTC),
        voting_deadline=datetime(2027, 1, 5, tzinfo=UTC),
    )
    if approved:
        governance.open_proposal(
            proposal.proposal_id, occurred_at=datetime(2027, 1, 2, tzinfo=UTC)
        )
        for voter in proposal.eligible_member_ids:
            governance.vote(
                proposal.proposal_id,
                voter,
                VoteChoice.YES,
                occurred_at=datetime(2027, 1, 3, tzinfo=UTC),
            )
        assert (
            governance.evaluate(
                proposal.proposal_id, occurred_at=datetime(2027, 1, 5, tzinfo=UTC)
            )
            is ProposalStatus.APPROVED
        )
    return governance, proposal.proposal_id


def registry() -> tuple[HybridExitRegistry, MemberUnitLedger]:
    unit_ledger = MemberUnitLedger()
    return (
        HybridExitRegistry(
            HybridAllocationRegistry(),
            HybridArrearsRegistry(),
            unit_ledger,
        ),
        unit_ledger,
    )


def record(
    exit_registry: HybridExitRegistry,
    *,
    governance: GovernanceRegistry,
    fee_rules: HybridRuleSchedule | None = None,
    due_date: date = date(2027, 1, 31),
) -> HybridExit:
    return exit_registry.record_exit(
        exit_id="exit-1",
        proposal_id="exit-decision",
        governance=governance,
        rules=fee_rules or rules(),
        payout_due_date=due_date,
        requested_at=NOW,
    )


def resolve(
    exit_registry: HybridExitRegistry,
    *,
    valuations: tuple[HybridUnitValuation, ...],
    payouts: tuple[ClassicPayout, ...] = (),
) -> HybridExit:
    return exit_registry.resolve_valuation(
        "exit-1",
        valuations=valuations,
        contribution_cycles=(),
        payouts=payouts,
        occurred_at=NOW,
    )


def valuation(
    valuation_id: str,
    effective_date: date,
    price: str = "100",
) -> HybridUnitValuation:
    return HybridUnitValuation(valuation_id, effective_date, Decimal(price), "XAF")


def test_exit_requires_approved_decision_and_freezes_allocations() -> None:
    unapproved, _ = approved_exit(approved=False)
    allocations = HybridAllocationRegistry()
    unit_ledger = MemberUnitLedger()
    exit_registry = HybridExitRegistry(
        allocations, HybridArrearsRegistry(), unit_ledger
    )
    with pytest.raises(ValueError, match="not approved"):
        record(exit_registry, governance=unapproved)

    governance, _ = approved_exit()
    record(exit_registry, governance=governance)
    assert exit_registry.exit_for("exit-1").status is ExitStatus.PENDING_VALUATION
    assert exit_registry.audit_events("exit-1")[0].event_type == (
        "hybrid_member_exit_recorded"
    )
    cycle = ContributionCycle(
        "cycle-after-exit",
        date(2027, 1, 1),
        date(2027, 1, 31),
        "UTC",
    )
    cycle.add_expected_contribution("member-a", Decimal("100"))
    cycle.record_contribution(
        "member-a", Decimal("100"), payment_date=datetime(2027, 1, 10, tzinfo=UTC)
    )
    with pytest.raises(ValueError, match="on or after exit"):
        allocations.allocate(
            allocation_id="allocation-1",
            contribution_id="contribution-1",
            cycle=cycle,
            member_id="member-a",
            cycle_number=2,
            rule_version=rules().version_for_cycle(2),
            valuations=(),
            unit_ledger=unit_ledger,
        )


def test_exit_uses_first_forward_valuation_and_request_cycle_fee() -> None:
    governance, _ = approved_exit()
    exit_registry, units = registry()
    units.issue_units("member-a", Decimal("100"), "seed-units")
    first_rule = HybridRule(
        "XAF",
        3000,
        Decimal("100"),
        30,
        exit_fees=ExitFeeSchedule(voluntary=Decimal("1")),
    )
    later_rule = HybridRule(
        "XAF",
        3000,
        Decimal("100"),
        30,
        exit_fees=ExitFeeSchedule(voluntary=Decimal("5")),
    )
    schedule = rules(
        versions=(
            HybridRuleVersion(1, 1, 0, first_rule),
            HybridRuleVersion(2, 4, 2, later_rule),
        )
    )
    record(exit_registry, governance=governance, fee_rules=schedule)

    resolved = resolve(
        exit_registry,
        valuations=(
            valuation("later", date(2027, 1, 20)),
            valuation("first", EXIT_DATE),
        ),
    )

    assert resolved.settlement.valuation_id == "first"
    assert resolved.settlement.gross_unit_value == Decimal("10000")
    assert resolved.settlement.exit_fee == Decimal("100")
    assert resolved.settlement.net_amount == Decimal("9900")
    assert resolved.settlement.lines[0] == ("gross_unit_value", Decimal("10000"))
    assert units.balance_for("member-a") == 0
    assert [event.event_type for event in exit_registry.audit_events("exit-1")] == [
        "hybrid_member_exit_recorded",
        "hybrid_exit_settled",
    ]


def test_missing_valuation_keeps_exit_pending_without_redeeming_units() -> None:
    governance, _ = approved_exit()
    exit_registry, units = registry()
    units.issue_units("member-a", Decimal("5"), "seed-units")
    record(exit_registry, governance=governance)

    pending = resolve(exit_registry, valuations=())

    assert pending.status is ExitStatus.PENDING_VALUATION
    assert pending.settlement is None
    assert units.balance_for("member-a") == Decimal("5")


def test_future_valuation_is_not_used_before_its_effective_date() -> None:
    governance, _ = approved_exit()
    exit_registry, units = registry()
    units.issue_units("member-a", Decimal("5"), "seed-units")
    record(exit_registry, governance=governance)
    future = valuation("future", date(2027, 1, 25))

    pending = resolve(exit_registry, valuations=(future,))
    assert pending.status is ExitStatus.PENDING_VALUATION

    settled = exit_registry.resolve_valuation(
        "exit-1",
        valuations=(future,),
        contribution_cycles=(),
        payouts=(),
        occurred_at=datetime(2027, 1, 25, tzinfo=UTC),
    )
    assert settled.settlement.valuation_id == "future"
    assert units.balance_for("member-a") == 0


def test_death_entitlement_waits_for_proof_then_queues_and_pays() -> None:
    governance, _ = approved_exit(exit_type=MemberExitType.DEATH)
    exit_registry, units = registry()
    units.issue_units("member-a", Decimal("10"), "seed-units")
    record(exit_registry, governance=governance)
    death_exit = resolve(exit_registry, valuations=(valuation("v1", EXIT_DATE),))
    assert death_exit.status is ExitStatus.HELD_FOR_ESTATE

    queued = exit_registry.record_estate_proof(
        "exit-1", "succession-judgment-1", occurred_at=NOW
    )
    assert queued.status is ExitStatus.QUEUED
    report = exit_registry.build_queue(
        "queue-1",
        currency="XAF",
        liquidity_cap=Decimal("999"),
        created_at=datetime(2027, 2, 1, tzinfo=UTC),
    )
    assert report.entries[0].amount == Decimal("1000")
    assert report.entries[0].status is ExitStatus.QUEUED
    next_report = exit_registry.build_queue(
        "queue-2",
        currency="XAF",
        liquidity_cap=Decimal("1000"),
        created_at=datetime(2027, 2, 2, tzinfo=UTC),
    )
    assert next_report.entries[0].status is ExitStatus.PAYABLE
    paid = exit_registry.record_external_payment(
        "exit-1", "payment-ref-1", occurred_at=datetime(2027, 2, 3, tzinfo=UTC)
    )
    assert paid.status is ExitStatus.PAID_EXTERNALLY
    assert units.balance_for("member-a") == 0


def test_negative_net_remains_visible_as_member_debt() -> None:
    governance, _ = approved_exit()
    exit_registry, units = registry()
    units.issue_units("member-a", Decimal("1"), "seed-units")
    record(exit_registry, governance=governance)
    payout = ClassicPayout(
        1,
        "member-a",
        Decimal("500"),
        "XAF",
        datetime(2027, 1, 9, tzinfo=UTC),
        "payout-event",
    )

    settled = resolve(
        exit_registry,
        valuations=(valuation("v1", EXIT_DATE),),
        payouts=(payout,),
    )

    assert settled.status is ExitStatus.AMOUNT_OWED
    assert settled.settlement.excess_pot_received == Decimal("500")
    assert settled.settlement.net_amount == Decimal("-400")


def test_death_fee_is_zero_and_cooperative_expulsion_fee_is_capped() -> None:
    governance, _ = approved_exit(exit_type=MemberExitType.DEATH)
    exit_registry, units = registry()
    units.issue_units("member-a", Decimal("1"), "seed-units")
    schedule = rules(fees=ExitFeeSchedule(voluntary=Decimal("10"), death=Decimal("0")))
    record(exit_registry, governance=governance, fee_rules=schedule)
    assert (
        resolve(
            exit_registry, valuations=(valuation("v1", EXIT_DATE),)
        ).settlement.exit_fee
        == 0
    )

    with pytest.raises(ValueError, match="Expulsion fee"):
        HybridRule(
            "XAF",
            3000,
            Decimal("100"),
            30,
            exit_fees=ExitFeeSchedule(voluntary=Decimal("5"), expulsion=Decimal("8")),
            legal_form=LegalForm.COOPERATIVE,
        )

    expulsion_governance, _ = approved_exit(exit_type=MemberExitType.EXPULSION)
    expulsion_registry, expulsion_units = registry()
    expulsion_units.issue_units("member-a", Decimal("1"), "expulsion-units")
    cooperative_rules = rules(
        fees=ExitFeeSchedule(voluntary=Decimal("10"), expulsion=Decimal("5")),
        legal_form=LegalForm.COOPERATIVE,
    )
    record(
        expulsion_registry,
        governance=expulsion_governance,
        fee_rules=cooperative_rules,
    )
    expulsion_settlement = resolve(
        expulsion_registry, valuations=(valuation("expulsion-v1", EXIT_DATE),)
    )
    assert expulsion_settlement.exit_type is MemberExitType.EXPULSION
    assert expulsion_settlement.settlement.exit_fee == Decimal("5")


def test_liquidity_queue_does_not_skip_an_earlier_unfunded_exit() -> None:
    members = ("member-a", "member-b", "member-c", "member-d", "member-e")
    governance = GovernanceRegistry(
        members, ClassicRotation.from_active_members(members)
    )
    for proposal_id, member_id in (
        ("decision-a", "member-a"),
        ("decision-b", "member-b"),
    ):
        proposal = governance.create_member_exit_proposal(
            proposal_id=proposal_id,
            title="Member exit",
            description="Approve exit.",
            proposer_id="member-c",
            member_id=member_id,
            exit_type=MemberExitType.VOLUNTARY,
            exit_date=EXIT_DATE,
            request_cycle=2,
            approval_threshold=Decimal("60"),
            created_at=datetime(2027, 1, 1, tzinfo=UTC),
            voting_deadline=datetime(2027, 1, 5, tzinfo=UTC),
        )
        governance.open_proposal(
            proposal_id, occurred_at=datetime(2027, 1, 2, tzinfo=UTC)
        )
        for voter in proposal.eligible_member_ids:
            governance.vote(
                proposal_id,
                voter,
                VoteChoice.YES,
                occurred_at=datetime(2027, 1, 3, tzinfo=UTC),
            )
        assert (
            governance.evaluate(
                proposal_id, occurred_at=datetime(2027, 1, 5, tzinfo=UTC)
            )
            is ProposalStatus.APPROVED
        )

    exit_registry, units = registry()
    units.issue_units("member-a", Decimal("6"), "units-a")
    units.issue_units("member-b", Decimal("4"), "units-b")
    for index, (proposal_id, member_id) in enumerate(
        (("decision-a", "member-a"), ("decision-b", "member-b"))
    ):
        exit_registry.record_exit(
            exit_id=f"exit-{index}",
            proposal_id=proposal_id,
            governance=governance,
            rules=rules(),
            payout_due_date=date(2027, 1, 31),
            requested_at=datetime(2027, 1, 20 + index, tzinfo=UTC),
        )
        exit_registry.resolve_valuation(
            f"exit-{index}",
            valuations=(valuation(f"v-{index}", EXIT_DATE),),
            contribution_cycles=(),
            payouts=(),
            occurred_at=NOW,
        )

    report = exit_registry.build_queue(
        "fifo-queue",
        currency="XAF",
        liquidity_cap=Decimal("500"),
        created_at=datetime(2027, 2, 1, tzinfo=UTC),
    )

    assert [entry.exit_id for entry in report.entries] == ["exit-0", "exit-1"]
    assert [entry.amount for entry in report.entries] == [
        Decimal("600"),
        Decimal("400"),
    ]
    assert [entry.status for entry in report.entries] == [
        ExitStatus.QUEUED,
        ExitStatus.QUEUED,
    ]


def test_disputed_estate_entitlement_can_be_consigned() -> None:
    governance, _ = approved_exit(exit_type=MemberExitType.DEATH)
    exit_registry, units = registry()
    units.issue_units("member-a", Decimal("2"), "seed-units")
    record(exit_registry, governance=governance)
    resolve(exit_registry, valuations=(valuation("v1", EXIT_DATE),))

    consigned = exit_registry.consign(
        "exit-1", "court-sequestration-1", occurred_at=NOW
    )

    assert consigned.status is ExitStatus.CONSIGNED
    assert consigned.consignment_reference == "court-sequestration-1"


def test_approved_reasoned_deferral_can_extend_due_date_to_24_months() -> None:
    governance, proposal_id = approved_exit()
    extended_date = date(2028, 1, 11)
    deferral = governance.create_payout_deferral_proposal(
        proposal_id="deferral-decision",
        title="Extend payout",
        description="Record a reasoned payout extension.",
        proposer_id="member-b",
        exit_proposal_id=proposal_id,
        reason="Liquidity constraints.",
        extended_date=extended_date,
        current_cycle=3,
        approval_threshold=Decimal("60"),
        created_at=datetime(2027, 1, 6, tzinfo=UTC),
        voting_deadline=datetime(2027, 1, 9, tzinfo=UTC),
    )
    governance.open_proposal(
        deferral.proposal_id, occurred_at=datetime(2027, 1, 7, tzinfo=UTC)
    )
    for voter in deferral.eligible_member_ids:
        governance.vote(
            deferral.proposal_id,
            voter,
            VoteChoice.YES,
            occurred_at=datetime(2027, 1, 8, tzinfo=UTC),
        )
    assert (
        governance.evaluate(
            deferral.proposal_id, occurred_at=datetime(2027, 1, 9, tzinfo=UTC)
        )
        is ProposalStatus.APPROVED
    )
    exit_registry, _ = registry()

    extended = exit_registry.record_exit(
        exit_id="exit-1",
        proposal_id=proposal_id,
        governance=governance,
        rules=rules(),
        payout_due_date=extended_date,
        requested_at=NOW,
        deferral_proposal_id="deferral-decision",
    )

    assert extended.payout_due_date == extended_date


@pytest.mark.parametrize(
    ("due_date", "extension", "message"),
    [
        (date(2028, 1, 11), None, "approved reasoned deferral"),
        (date(2029, 1, 11), "extension", "within 24 months"),
    ],
)
def test_exit_deferral_limits(
    due_date: date, extension: str | None, message: str
) -> None:
    governance, _ = approved_exit()
    exit_registry, _ = registry()
    with pytest.raises(ValueError, match=message):
        exit_registry.record_exit(
            exit_id="exit-1",
            proposal_id="exit-decision",
            governance=governance,
            rules=rules(),
            payout_due_date=due_date,
            requested_at=NOW,
            deferral_proposal_id=extension,
        )


def test_exit_snapshot_restores_pending_exit_and_audit_history() -> None:
    governance, _ = approved_exit()
    allocations = HybridAllocationRegistry()
    arrears = HybridArrearsRegistry()
    units = MemberUnitLedger()
    exit_registry = HybridExitRegistry(allocations, arrears, units)
    record(exit_registry, governance=governance)

    snapshot = exit_registry.snapshot()
    restored = snapshot.restore(
        allocation_registry=allocations,
        arrears_registry=arrears,
        unit_ledger=units,
    )

    assert isinstance(snapshot, HybridExitSnapshot)
    assert restored.snapshot() == snapshot
    assert restored.exit_for("exit-1").status is ExitStatus.PENDING_VALUATION


def test_exit_snapshot_restores_settlement_queue_and_payment_transition() -> None:
    governance, _ = approved_exit()
    allocations = HybridAllocationRegistry()
    arrears = HybridArrearsRegistry()
    units = MemberUnitLedger()
    exit_registry = HybridExitRegistry(allocations, arrears, units)
    units.issue_units("member-a", Decimal("5"), "seed-units")
    record(exit_registry, governance=governance)
    exit_registry.resolve_valuation(
        "exit-1",
        valuations=(valuation("v1", EXIT_DATE),),
        contribution_cycles=(),
        payouts=(),
        occurred_at=NOW,
    )
    exit_registry.build_queue(
        "queue-1",
        currency="XAF",
        liquidity_cap=Decimal("1000"),
        created_at=datetime(2027, 1, 31, 12, tzinfo=UTC),
    )
    snapshot = exit_registry.snapshot()

    restored = snapshot.restore(
        allocation_registry=allocations,
        arrears_registry=arrears,
        unit_ledger=units,
    )

    assert restored.snapshot() == snapshot
    assert restored.queue_reports() == exit_registry.queue_reports()
    assert [event.event_type for event in restored.audit_events("queue-1")] == [
        "hybrid_exit_queue_reported"
    ]
    paid = restored.record_external_payment(
        "exit-1",
        "payment-1",
        occurred_at=datetime(2027, 1, 31, 12, tzinfo=UTC),
    )
    assert paid.status is ExitStatus.PAID_EXTERNALLY
    assert restored.snapshot().exits[0].external_payment_reference == "payment-1"


def test_exit_snapshot_restore_requires_matching_unit_redemption_event() -> None:
    governance, _ = approved_exit()
    allocations = HybridAllocationRegistry()
    arrears = HybridArrearsRegistry()
    units = MemberUnitLedger()
    exit_registry = HybridExitRegistry(allocations, arrears, units)
    units.issue_units("member-a", Decimal("5"), "seed-units")
    record(exit_registry, governance=governance)
    exit_registry.resolve_valuation(
        "exit-1",
        valuations=(valuation("v1", EXIT_DATE),),
        contribution_cycles=(),
        payouts=(),
        occurred_at=NOW,
    )

    with pytest.raises(ValueError, match="unit event"):
        exit_registry.snapshot().restore(
            allocation_registry=allocations,
            arrears_registry=arrears,
            unit_ledger=MemberUnitLedger(),
        )
