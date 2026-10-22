from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from tontine.classic import ClassicRotation
from tontine.governance import (
    GovernanceRegistry,
    MemberExitEffect,
    MemberExitType,
    PayoutDeferralEffect,
    PenaltyWaiverEffect,
    ProposalStatus,
    RotationProposal,
    VoteChoice,
)

MEMBERS = ("member-a", "member-b", "member-c", "member-d", "member-e")
CREATED_AT = datetime(2027, 1, 1, tzinfo=UTC)
OPENED_AT = datetime(2027, 1, 2, tzinfo=UTC)
VOTED_AT = datetime(2027, 1, 3, tzinfo=UTC)
DEADLINE = datetime(2027, 1, 10, tzinfo=UTC)
EXIT_DATE = date(2027, 1, 1)


def registry(member_ids: tuple[str, ...] = MEMBERS) -> GovernanceRegistry:
    return GovernanceRegistry(
        member_ids,
        ClassicRotation.from_active_members(member_ids),
    )


def create_exit(
    governance: GovernanceRegistry,
    proposal_id: str = "exit",
    *,
    member_id: str = "member-a",
    exit_type: MemberExitType = MemberExitType.VOLUNTARY,
) -> RotationProposal:
    return governance.create_member_exit_proposal(
        proposal_id=proposal_id,
        title="Member exit",
        description="Approve the requested member exit.",
        proposer_id="member-b" if member_id == "member-a" else "member-a",
        member_id=member_id,
        exit_type=exit_type,
        exit_date=EXIT_DATE,
        request_cycle=2,
        approval_threshold=Decimal("60"),
        created_at=CREATED_AT,
        voting_deadline=DEADLINE,
    )


def decide(
    governance: GovernanceRegistry,
    proposal: RotationProposal,
    *,
    choices: dict[str, VoteChoice] | None = None,
) -> ProposalStatus:
    opened_at = max(OPENED_AT, proposal.created_at + timedelta(days=1))
    voted_at = opened_at + timedelta(days=1)
    governance.open_proposal(proposal.proposal_id, occurred_at=opened_at)
    for member_id in proposal.eligible_member_ids:
        governance.vote(
            proposal.proposal_id,
            member_id,
            (choices or {}).get(member_id, VoteChoice.YES),
            occurred_at=voted_at,
        )
    return governance.evaluate(
        proposal.proposal_id, occurred_at=max(DEADLINE, proposal.voting_deadline)
    )


def create_waiver(
    governance: GovernanceRegistry,
    proposal_id: str = "waiver",
    *,
    assessment_id: str = "penalty-1",
    member_id: str = "member-a",
) -> RotationProposal:
    return governance.create_penalty_waiver_proposal(
        proposal_id=proposal_id,
        title="Waive penalty",
        description="Review the member's waiver request.",
        proposer_id="member-b" if member_id == "member-a" else "member-a",
        penalty_assessment_id=assessment_id,
        member_id=member_id,
        current_cycle=2,
        approval_threshold=Decimal("60"),
        created_at=CREATED_AT,
        voting_deadline=DEADLINE,
    )


def create_deferral(
    governance: GovernanceRegistry,
    *,
    proposal_id: str = "deferral",
    exit_proposal_id: str = "exit",
    extended_date: date = date(2029, 1, 1),
    reason: str = "Liquidity constraint approved by the group.",
) -> RotationProposal:
    return governance.create_payout_deferral_proposal(
        proposal_id=proposal_id,
        title="Extend payout date",
        description="Record the approved payout extension.",
        proposer_id="member-b",
        exit_proposal_id=exit_proposal_id,
        reason=reason,
        extended_date=extended_date,
        current_cycle=3,
        approval_threshold=Decimal("60"),
        created_at=datetime(2027, 1, 11, tzinfo=UTC),
        voting_deadline=datetime(2027, 1, 20, tzinfo=UTC),
    )


def test_approved_exit_is_typed_audited_and_available_by_decision_id() -> None:
    governance = registry()
    proposal = create_exit(governance, exit_type=MemberExitType.DEATH)

    assert proposal.eligible_member_ids == MEMBERS
    assert decide(governance, proposal) is ProposalStatus.APPROVED
    assert governance.approved_member_exit("exit") == MemberExitEffect(
        "member-a", MemberExitType.DEATH, EXIT_DATE, 2
    )
    event = next(
        event
        for event in governance.audit_events("exit")
        if event.event_type == "member_exit_approved"
    )
    assert event.details == {
        "member_id": "member-a",
        "exit_type": "death",
        "exit_date": "2027-01-01",
        "request_cycle": 2,
    }


def test_rejected_exit_has_no_approved_effect() -> None:
    governance = registry()
    proposal = create_exit(governance)
    choices = {
        member: VoteChoice.YES if member in {"member-a", "member-b"} else VoteChoice.NO
        for member in MEMBERS
    }

    assert decide(governance, proposal, choices=choices) is ProposalStatus.REJECTED
    with pytest.raises(ValueError, match="not approved"):
        governance.approved_member_exit("exit")
    assert not any(
        event.event_type == "member_exit_approved"
        for event in governance.audit_events("exit")
    )


def test_expulsion_recuses_member_and_preserves_electorate_snapshot() -> None:
    governance = registry()
    proposal = create_exit(governance, exit_type=MemberExitType.EXPULSION)
    assert proposal.eligible_member_ids == (
        "member-b",
        "member-c",
        "member-d",
        "member-e",
    )
    governance.open_proposal("exit", occurred_at=OPENED_AT)

    with pytest.raises(ValueError, match="frozen electorate"):
        governance.vote("exit", "member-a", VoteChoice.YES, occurred_at=VOTED_AT)

    governance.set_active_members(
        ("member-a", "member-b", "member-c", "member-d", "member-f"),
        occurred_at=VOTED_AT,
    )
    snapshot = governance.snapshot()
    restored = GovernanceRegistry.from_snapshot(snapshot)
    saved = next(
        item for item in restored.snapshot().proposals if item.proposal_id == "exit"
    )

    assert saved.eligible_member_ids == (
        "member-b",
        "member-c",
        "member-d",
        "member-e",
    )


@pytest.mark.parametrize("exit_type", (MemberExitType.VOLUNTARY, MemberExitType.DEATH))
def test_non_expulsion_exit_does_not_restrict_electorate(
    exit_type: MemberExitType,
) -> None:
    proposal = create_exit(registry(), exit_type=exit_type)

    assert proposal.eligible_member_ids == MEMBERS


def test_waiver_recuses_assessed_member_and_is_available_after_approval() -> None:
    governance = registry()
    proposal = create_waiver(governance)
    assert "member-a" not in proposal.eligible_member_ids

    governance.open_proposal("waiver", occurred_at=OPENED_AT)
    with pytest.raises(ValueError, match="frozen electorate"):
        governance.vote("waiver", "member-a", VoteChoice.YES, occurred_at=VOTED_AT)
    for member_id in proposal.eligible_member_ids:
        governance.vote("waiver", member_id, VoteChoice.YES, occurred_at=VOTED_AT)
    assert (
        governance.evaluate("waiver", occurred_at=DEADLINE) is ProposalStatus.APPROVED
    )
    expected = PenaltyWaiverEffect("penalty-1", "member-a")
    assert governance.approved_penalty_waiver("waiver") == expected
    restored = GovernanceRegistry.from_snapshot(governance.snapshot())
    assert restored.approved_penalty_waiver("waiver") == expected


def test_waiver_rejects_duplicate_assessments_and_allows_other_members_to_vote() -> (
    None
):
    governance = registry()
    proposal = create_waiver(governance)
    assert len(proposal.eligible_member_ids) == len(MEMBERS) - 1
    with pytest.raises(ValueError, match="matching member decision"):
        create_waiver(governance, "duplicate-waiver")

    governance = registry()
    proposal = create_waiver(
        governance,
        "other-waiver",
        member_id="member-e",
        assessment_id="penalty-2",
    )
    assert "member-a" in proposal.eligible_member_ids
    governance.open_proposal("other-waiver", occurred_at=OPENED_AT)
    governance.vote("other-waiver", "member-a", VoteChoice.YES, occurred_at=VOTED_AT)
    assert proposal.votes == {"member-a": VoteChoice.YES}


def test_deferral_requires_approved_exit_reason_and_date_within_24_months() -> None:
    governance = registry()
    exit_proposal = create_exit(governance)
    assert decide(governance, exit_proposal) is ProposalStatus.APPROVED

    with pytest.raises(ValueError, match="after 12 months"):
        create_deferral(governance, extended_date=date(2028, 1, 1))
    with pytest.raises(ValueError, match="within 24 months"):
        create_deferral(governance, extended_date=date(2029, 1, 2))
    with pytest.raises(ValueError, match="reason is required"):
        create_deferral(governance, reason=" ")

    proposal = create_deferral(governance)
    assert decide(governance, proposal) is ProposalStatus.APPROVED
    assert governance.approved_payout_deferral("deferral") == PayoutDeferralEffect(
        "exit",
        "Liquidity constraint approved by the group.",
        date(2029, 1, 1),
    )
    assert (
        GovernanceRegistry.from_snapshot(
            governance.snapshot()
        ).approved_payout_deferral("deferral")
        == proposal.effect
    )


def test_deferral_requires_an_approved_exit_and_proposal_is_decision_specific() -> None:
    governance = registry()
    create_exit(governance)
    with pytest.raises(ValueError, match="not approved"):
        create_deferral(governance)

    approved_exit = registry()
    exit_proposal = create_exit(approved_exit)
    assert decide(approved_exit, exit_proposal) is ProposalStatus.APPROVED
    deferral = create_deferral(approved_exit)
    with pytest.raises(ValueError, match="not approved"):
        approved_exit.approved_payout_deferral(deferral.proposal_id)
    with pytest.raises(ValueError, match="matching member decision"):
        create_deferral(approved_exit, proposal_id="duplicate-deferral")


def test_snapshot_rejects_an_electorate_that_includes_a_recused_member() -> None:
    governance = registry()
    create_exit(governance, exit_type=MemberExitType.EXPULSION)
    snapshot = governance.snapshot()
    saved = snapshot.proposals[0]
    forged_proposal = replace(
        saved,
        eligible_member_ids=tuple(sorted((*saved.eligible_member_ids, "member-a"))),
    )
    forged_snapshot = replace(snapshot, proposals=(forged_proposal,))

    with pytest.raises(ValueError, match="Interested member"):
        GovernanceRegistry.from_snapshot(forged_snapshot)
