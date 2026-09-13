from datetime import UTC, datetime
from decimal import Decimal

import pytest

from tontine.audit import AuditEventRegistry
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


def test_governance_uses_shared_audit_registry() -> None:
    audit_registry = AuditEventRegistry()
    governance = GovernanceRegistry(
        active_member_ids=("member-a",),
        initial_rotation=ClassicRotation.from_active_members(("member-a",)),
        audit_registry=audit_registry,
    )

    governance.create_rotation_proposal(
        proposal_id="proposal-shared",
        title="Shared audit",
        description="Use the canonical audit registry.",
        proposer_id="member-a",
        rotation_order=("member-a",),
        approval_threshold=Decimal("100"),
        effective_cycle=2,
        created_at=datetime(2027, 1, 1, tzinfo=UTC),
        voting_deadline=datetime(2027, 1, 2, tzinfo=UTC),
    )

    assert audit_registry.events_for("proposal", "proposal-shared")


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


def test_governance_rejects_invalid_proposal_lifecycle_and_missing_ids(
    governance: GovernanceRegistry,
) -> None:
    with pytest.raises(KeyError, match="not found"):
        governance.open_proposal("missing")
    with pytest.raises(ValueError, match="active members"):
        GovernanceRegistry((), ClassicRotation.from_active_members(("member-a",)))

    arguments = {
        "proposal_id": "proposal-invalid",
        "title": "Invalid",
        "description": "Invalid proposal",
        "proposer_id": "member-a",
        "rotation_order": ("member-a", "member-b", "member-c", "member-d", "member-e"),
        "approval_threshold": Decimal("60"),
        "effective_cycle": 2,
        "created_at": datetime(2027, 1, 2, tzinfo=UTC),
        "voting_deadline": datetime(2027, 1, 3, tzinfo=UTC),
    }
    governance.create_rotation_proposal(**arguments)
    with pytest.raises(ValueError, match="already exists"):
        governance.create_rotation_proposal(**arguments)
    with pytest.raises(ValueError, match="open"):
        governance.vote("proposal-invalid", "member-a", VoteChoice.YES)
    governance.open_proposal("proposal-invalid")
    with pytest.raises(ValueError, match="open"):
        governance.open_proposal("proposal-invalid")


def test_governance_rejects_invalid_proposal_inputs(governance: GovernanceRegistry) -> None:
    base = {
        "proposal_id": "proposal-invalid",
        "title": "Invalid",
        "description": "Invalid proposal",
        "proposer_id": "member-a",
        "rotation_order": ("member-a", "member-b", "member-c", "member-d", "member-e"),
        "approval_threshold": Decimal("60"),
        "effective_cycle": 2,
        "created_at": datetime(2027, 1, 2, tzinfo=UTC),
        "voting_deadline": datetime(2027, 1, 3, tzinfo=UTC),
    }
    with pytest.raises(ValueError, match="eligible"):
        governance.create_rotation_proposal(**{**base, "proposer_id": "missing"})
    with pytest.raises(ValueError, match="timezone-aware"):
        governance.create_rotation_proposal(
            **{**base, "created_at": datetime(2027, 1, 2)}
        )
    with pytest.raises(ValueError, match="cycle and dates"):
        governance.create_rotation_proposal(
            **{**base, "effective_cycle": 0}
        )


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

    empty_governance = GovernanceRegistry(
        ("member-a",), ClassicRotation.from_active_members(("member-a",))
    )
    with pytest.raises(KeyError, match="No ruleset"):
        empty_governance.ruleset_for_cycle(1)
    with pytest.raises(ValueError, match="identifier"):
        Ruleset("", 1, 1, {})
    with pytest.raises(ValueError, match="positive"):
        Ruleset("rules-invalid", 0, 1, {})
