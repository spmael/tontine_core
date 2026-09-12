from datetime import UTC, datetime
from decimal import Decimal

import pytest

from tontine.classic import ClassicRotation
from tontine.governance import (
    GovernanceRegistry,
    ProposalStatus,
    Ruleset,
    VoteChoice,
)


@pytest.fixture
def governance() -> GovernanceRegistry:
    return GovernanceRegistry(
        active_member_ids=("member-a", "member-b", "member-c", "member-d", "member-e"),
        initial_rotation=ClassicRotation.from_active_members(
            ("member-a", "member-b", "member-c", "member-d", "member-e")
        ),
    )


def test_rotation_proposal_requires_votes_and_activates_at_effective_cycle(
    governance: GovernanceRegistry,
) -> None:
    proposal = governance.create_rotation_proposal(
        proposal_id="proposal-1",
        title="New rotation",
        description="Approve a new recipient order.",
        proposer_id="member-a",
        rotation_order=("member-e", "member-d", "member-c", "member-b", "member-a"),
        approval_threshold=Decimal("60"),
        effective_cycle=6,
        created_at=datetime(2027, 1, 1, tzinfo=UTC),
        voting_deadline=datetime(2027, 1, 15, tzinfo=UTC),
    )
    governance.open_proposal("proposal-1")

    assert governance.rotation_for_cycle(5).recipient_for_cycle(5) == "member-e"
    assert governance.rotation_for_cycle(6).recipient_for_cycle(6) == "member-a"

    for member_id in ("member-a", "member-b", "member-c"):
        governance.vote("proposal-1", member_id, VoteChoice.YES)

    assert governance.evaluate("proposal-1") is ProposalStatus.APPROVED
    activated = governance.rotation_for_cycle(6)
    assert activated.recipient_for_cycle(1) == "member-e"
    assert governance.audit_events("proposal-1")
    assert proposal.status is ProposalStatus.APPROVED


def test_governance_rejects_duplicate_and_ineligible_votes(
    governance: GovernanceRegistry,
) -> None:
    governance.create_rotation_proposal(
        proposal_id="proposal-1",
        title="New rotation",
        description="Approve a new recipient order.",
        proposer_id="member-a",
        rotation_order=("member-e", "member-d", "member-c", "member-b", "member-a"),
        approval_threshold=Decimal("60"),
        effective_cycle=6,
        created_at=datetime(2027, 1, 1, tzinfo=UTC),
        voting_deadline=datetime(2027, 1, 15, tzinfo=UTC),
    )
    governance.open_proposal("proposal-1")
    governance.vote("proposal-1", "member-a", VoteChoice.YES)

    with pytest.raises(ValueError, match="already voted"):
        governance.vote("proposal-1", "member-a", VoteChoice.NO)
    with pytest.raises(ValueError, match="eligible"):
        governance.vote("proposal-1", "member-x", VoteChoice.YES)


def test_rotation_proposal_rejects_invalid_threshold_and_order(
    governance: GovernanceRegistry,
) -> None:
    with pytest.raises(ValueError, match="threshold"):
        governance.create_rotation_proposal(
            proposal_id="proposal-1",
            title="Invalid",
            description="Invalid threshold",
            proposer_id="member-a",
            rotation_order=("member-a", "member-b", "member-c", "member-d", "member-e"),
            approval_threshold=Decimal("101"),
            effective_cycle=6,
            created_at=datetime(2027, 1, 1, tzinfo=UTC),
            voting_deadline=datetime(2027, 1, 15, tzinfo=UTC),
        )


def test_rulesets_are_versioned_by_effective_cycle(
    governance: GovernanceRegistry,
) -> None:
    governance.add_ruleset(
        Ruleset("rules-v1", 1, 1, {"contribution_amount": "30000"})
    )
    governance.add_ruleset(
        Ruleset("rules-v2", 2, 6, {"contribution_amount": "35000"})
    )

    assert governance.ruleset_for_cycle(5).ruleset_id == "rules-v1"
    assert governance.ruleset_for_cycle(6).ruleset_id == "rules-v2"

    with pytest.raises(ValueError, match="(?i)rotation"):
        governance.create_rotation_proposal(
            proposal_id="proposal-2",
            title="Invalid",
            description="Invalid order",
            proposer_id="member-a",
            rotation_order=("member-a", "member-a"),
            approval_threshold=Decimal("60"),
            effective_cycle=6,
            created_at=datetime(2027, 1, 1, tzinfo=UTC),
            voting_deadline=datetime(2027, 1, 15, tzinfo=UTC),
        )
