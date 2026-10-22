from datetime import UTC, datetime
from decimal import Decimal

import pytest

from tontine.classic import ClassicRotation
from tontine.exceptions import MissingRecordError
from tontine.governance import (
    GovernanceRegistry,
    ProposalStatus,
    RotationProposal,
    VoteChoice,
)

CREATED_AT = datetime(2027, 1, 1, tzinfo=UTC)
OPENED_AT = datetime(2027, 1, 2, tzinfo=UTC)
DEADLINE = datetime(2027, 1, 10, tzinfo=UTC)
VOTE_AT = datetime(2027, 1, 3, tzinfo=UTC)


def registry(
    member_ids: tuple[str, ...] = (
        "member-a",
        "member-b",
        "member-c",
        "member-d",
        "member-e",
    ),
) -> GovernanceRegistry:
    return GovernanceRegistry(
        active_member_ids=member_ids,
        initial_rotation=ClassicRotation.from_active_members(member_ids),
    )


def create_proposal(
    governance: GovernanceRegistry,
    proposal_id: str = "proposal-1",
    *,
    effective_cycle: int = 2,
    current_cycle: int = 1,
    approval_threshold: Decimal = Decimal("60"),
    quorum_numerator: int = 2,
    quorum_denominator: int = 3,
    rotation_order: tuple[str, ...] = (
        "member-a",
        "member-b",
        "member-c",
        "member-d",
        "member-e",
    ),
) -> RotationProposal:
    return governance.create_rotation_proposal(
        proposal_id=proposal_id,
        title="Rotation update",
        description="Approve an updated rotation.",
        proposer_id="member-a",
        rotation_order=rotation_order,
        approval_threshold=approval_threshold,
        effective_cycle=effective_cycle,
        current_cycle=current_cycle,
        created_at=CREATED_AT,
        voting_deadline=DEADLINE,
        quorum_numerator=quorum_numerator,
        quorum_denominator=quorum_denominator,
    )


def test_quorum_rounds_up_and_abstentions_count_only_toward_participation() -> None:
    governance = registry()
    create_proposal(governance, approval_threshold=Decimal("40"))
    governance.open_proposal("proposal-1", occurred_at=OPENED_AT)

    for member_id, choice in (
        ("member-a", VoteChoice.YES),
        ("member-b", VoteChoice.YES),
        ("member-c", VoteChoice.NO),
        ("member-d", VoteChoice.ABSTAIN),
    ):
        governance.vote(
            "proposal-1",
            member_id,
            choice,
            occurred_at=VOTE_AT,
        )

    with pytest.raises(ValueError, match="every eligible member"):
        governance.evaluate("proposal-1", occurred_at=datetime(2027, 1, 5, tzinfo=UTC))

    assert (
        governance.evaluate("proposal-1", occurred_at=DEADLINE)
        is ProposalStatus.APPROVED
    )
    tally = governance.evaluation_for_proposal("proposal-1").tally
    assert tally.eligible_count == 5
    assert tally.yes_count == 2
    assert tally.no_count == 1
    assert tally.abstain_count == 1
    assert tally.non_voting_count == 1
    assert tally.participation_count == 4
    assert tally.quorum_required == 4
    assert tally.quorum_met
    assert tally.threshold_met
    assert tally.approved


def test_quorum_rejects_threshold_pass_without_enough_participation() -> None:
    governance = registry()
    create_proposal(governance, approval_threshold=Decimal("60"))
    governance.open_proposal("proposal-1", occurred_at=OPENED_AT)
    for member_id in ("member-a", "member-b", "member-c"):
        governance.vote(
            "proposal-1",
            member_id,
            VoteChoice.YES,
            occurred_at=VOTE_AT,
        )

    assert (
        governance.evaluate("proposal-1", occurred_at=DEADLINE)
        is ProposalStatus.REJECTED
    )
    tally = governance.tally_for_proposal("proposal-1")
    assert tally.threshold_met
    assert not tally.quorum_met
    assert not tally.approved


def test_zero_quorum_preserves_threshold_only_approval_behavior() -> None:
    governance = registry()
    create_proposal(
        governance,
        approval_threshold=Decimal("20"),
        quorum_numerator=0,
        quorum_denominator=1,
    )
    governance.open_proposal("proposal-1", occurred_at=OPENED_AT)
    governance.vote(
        "proposal-1",
        "member-a",
        VoteChoice.YES,
        occurred_at=VOTE_AT,
    )

    assert (
        governance.evaluate("proposal-1", occurred_at=DEADLINE)
        is ProposalStatus.APPROVED
    )
    assert governance.tally_for_proposal("proposal-1").quorum_required == 0


def test_membership_changes_do_not_rewrite_existing_proposal_electorates() -> None:
    governance = registry()
    create_proposal(governance)
    governance.set_active_members(
        ("member-a", "member-b", "member-c", "member-d", "member-x"),
        occurred_at=datetime(2027, 1, 2, tzinfo=UTC),
    )
    governance.open_proposal("proposal-1", occurred_at=OPENED_AT)

    governance.vote(
        "proposal-1",
        "member-e",
        VoteChoice.YES,
        occurred_at=VOTE_AT,
    )
    with pytest.raises(ValueError, match="frozen electorate"):
        governance.vote(
            "proposal-1",
            "member-x",
            VoteChoice.YES,
            occurred_at=VOTE_AT,
        )

    second = create_proposal(
        governance,
        "proposal-2",
        effective_cycle=3,
        rotation_order=("member-a", "member-b", "member-c", "member-d", "member-x"),
    )
    assert "member-x" in second.eligible_member_ids
    assert "member-e" not in second.eligible_member_ids


def test_proposals_require_strictly_future_effective_cycles() -> None:
    governance = registry()
    with pytest.raises(ValueError, match="greater than current cycle"):
        create_proposal(governance, current_cycle=2, effective_cycle=2)
    with pytest.raises(ValueError, match="greater than current cycle"):
        create_proposal(governance, current_cycle=3, effective_cycle=2)
    with pytest.raises(MissingRecordError, match="not found"):
        governance.evaluation_for_proposal("missing")


def test_votes_at_deadline_are_allowed_but_later_votes_are_rejected() -> None:
    governance = registry()
    create_proposal(governance)
    governance.open_proposal("proposal-1", occurred_at=OPENED_AT)

    governance.vote(
        "proposal-1",
        "member-a",
        VoteChoice.YES,
        occurred_at=DEADLINE,
    )
    with pytest.raises(ValueError, match="after the proposal deadline"):
        governance.vote(
            "proposal-1",
            "member-b",
            VoteChoice.YES,
            occurred_at=datetime(2027, 1, 11, tzinfo=UTC),
        )


def test_open_proposal_rejects_occurrence_time_after_deadline() -> None:
    governance = registry()
    create_proposal(governance)

    with pytest.raises(ValueError, match="within its lifecycle"):
        governance.open_proposal(
            "proposal-1",
            occurred_at=datetime(2027, 1, 11, tzinfo=UTC),
        )
