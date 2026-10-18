from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from tontine.audit import AuditEventRegistry
from tontine.classic import ClassicRotation
from tontine.exceptions import MissingRecordError
from tontine.governance import (
    GovernanceRegistry,
    GovernanceSnapshot,
    ProposalStatus,
    RotationExceptionEffect,
    RotationProposal,
    Ruleset,
    RulesetActivationEffect,
    VoteChoice,
)

MEMBERS = ("member-a", "member-b", "member-c", "member-d", "member-e")
CREATED_AT = datetime(2027, 1, 1, tzinfo=UTC)
OPENED_AT = datetime(2027, 1, 2, tzinfo=UTC)
VOTED_AT = datetime(2027, 1, 3, tzinfo=UTC)
DEADLINE = datetime(2027, 1, 10, tzinfo=UTC)


def registry() -> GovernanceRegistry:
    return GovernanceRegistry(
        MEMBERS,
        ClassicRotation.from_active_members(MEMBERS),
    )


def create_exception_proposal(
    governance: GovernanceRegistry,
    proposal_id: str = "exception-proposal",
) -> RotationProposal:
    return governance.create_rotation_exception_proposal(
        proposal_id=proposal_id,
        title="One-cycle recipient change",
        description="Change only the recipient for cycle two.",
        proposer_id="member-a",
        exception_id=f"exception-{proposal_id}",
        recipient_id="member-e",
        cycle_number=2,
        current_cycle=1,
        approval_threshold=Decimal("60"),
        created_at=CREATED_AT,
        voting_deadline=DEADLINE,
    )


def create_ruleset_proposal(
    governance: GovernanceRegistry,
    proposal_id: str,
    ruleset: Ruleset,
) -> RotationProposal:
    return governance.create_ruleset_proposal(
        proposal_id=proposal_id,
        title="Activate updated rules",
        description="Approve an immutable rule version.",
        proposer_id="member-a",
        ruleset=ruleset,
        current_cycle=1,
        approval_threshold=Decimal("60"),
        created_at=CREATED_AT,
        voting_deadline=DEADLINE,
    )


def decide(
    governance: GovernanceRegistry,
    proposal_id: str,
    *,
    choices: tuple[VoteChoice, ...] = (
        VoteChoice.YES,
        VoteChoice.YES,
        VoteChoice.YES,
        VoteChoice.ABSTAIN,
    ),
) -> ProposalStatus:
    governance.open_proposal(proposal_id, occurred_at=OPENED_AT)
    for member_id, choice in zip(MEMBERS, choices, strict=False):
        governance.vote(
            proposal_id,
            member_id,
            choice,
            occurred_at=VOTED_AT,
        )
    return governance.evaluate(proposal_id, occurred_at=DEADLINE)


def test_approved_exception_changes_only_one_cycle_recipient() -> None:
    governance = registry()
    proposal = create_exception_proposal(governance)
    assert isinstance(proposal.effect, RotationExceptionEffect)
    assert proposal.rotation_order == ()
    assert governance.resolve_rotation_for_cycle(2).exception is None

    assert decide(governance, "exception-proposal") is ProposalStatus.APPROVED

    resolved = governance.resolve_rotation_for_cycle(2)
    assert resolved.recipient_id == "member-e"
    assert resolved.rotation_version.rotation.recipient_for_cycle(2) == "member-b"
    assert resolved.exception is not None
    assert resolved.exception.proposal_id == "exception-proposal"
    assert governance.resolve_rotation_for_cycle(3).exception is None
    approval_events = governance.audit_events("exception-proposal")
    approval = next(
        event
        for event in approval_events
        if event.event_type == "rotation_exception_approved"
    )
    assert resolved.exception.approval_event_id == approval.event_id


def test_rejected_exception_does_not_change_rotation() -> None:
    governance = registry()
    create_exception_proposal(governance)

    assert (
        decide(
            governance,
            "exception-proposal",
            choices=(
                VoteChoice.YES,
                VoteChoice.YES,
                VoteChoice.NO,
                VoteChoice.NO,
            ),
        )
        is ProposalStatus.REJECTED
    )
    assert governance.resolve_rotation_for_cycle(2).recipient_id == "member-b"
    assert governance.resolve_rotation_for_cycle(2).exception is None


def test_evaluation_time_cannot_precede_the_latest_vote() -> None:
    governance = registry()
    create_exception_proposal(governance)
    governance.open_proposal("exception-proposal", occurred_at=OPENED_AT)
    for member_id in MEMBERS:
        governance.vote(
            "exception-proposal",
            member_id,
            VoteChoice.YES,
            occurred_at=VOTED_AT,
        )

    with pytest.raises(ValueError, match="cannot precede its latest vote"):
        governance.evaluate("exception-proposal", occurred_at=OPENED_AT)
    assert governance.snapshot().proposals[0].status is ProposalStatus.OPEN


def test_exception_proposals_reject_cycle_and_identifier_conflicts() -> None:
    governance = registry()
    create_exception_proposal(governance)
    with pytest.raises(ValueError, match="pending exception"):
        create_exception_proposal(governance, "exception-proposal-2")

    governance_reuse = registry()
    governance_reuse.create_rotation_exception_proposal(
        proposal_id="exception-a",
        title="Override A",
        description="Use cycle two.",
        proposer_id="member-a",
        exception_id="same-exception",
        recipient_id="member-e",
        cycle_number=2,
        current_cycle=1,
        approval_threshold=Decimal("60"),
        created_at=CREATED_AT,
        voting_deadline=DEADLINE,
    )
    with pytest.raises(ValueError, match="pending exception"):
        governance_reuse.create_rotation_exception_proposal(
            proposal_id="exception-b",
            title="Override B",
            description="Use cycle three.",
            proposer_id="member-a",
            exception_id="same-exception",
            recipient_id="member-e",
            cycle_number=3,
            current_cycle=1,
            approval_threshold=Decimal("60"),
            created_at=CREATED_AT,
            voting_deadline=DEADLINE,
        )


def test_ruleset_effect_is_applied_only_after_approval() -> None:
    governance = registry()
    ruleset = Ruleset("rules-v2", 2, 3, {"unpaid_policy": "allow"})
    proposal = create_ruleset_proposal(governance, "rules-proposal", ruleset)
    assert isinstance(proposal.effect, RulesetActivationEffect)
    with pytest.raises(ValueError, match="pending proposal"):
        governance.add_ruleset(
            ruleset,
            occurred_at=datetime(2027, 1, 2, tzinfo=UTC),
        )
    with pytest.raises(MissingRecordError, match="No ruleset"):
        governance.ruleset_for_cycle(3)

    assert (
        decide(
            governance,
            "rules-proposal",
            choices=(
                VoteChoice.YES,
                VoteChoice.YES,
                VoteChoice.NO,
                VoteChoice.NO,
            ),
        )
        is ProposalStatus.REJECTED
    )
    with pytest.raises(MissingRecordError, match="No ruleset"):
        governance.ruleset_for_cycle(3)

    governance_approved = registry()
    create_ruleset_proposal(governance_approved, "rules-approved", ruleset)
    assert decide(governance_approved, "rules-approved") is ProposalStatus.APPROVED
    assert governance_approved.ruleset_for_cycle(3) == ruleset
    assert any(
        event.event_type == "ruleset_activated"
        for event in governance_approved.audit_events("rules-approved")
    )


def test_snapshot_round_trip_preserves_proposals_effects_and_audit_order() -> None:
    governance = registry()
    initial_ruleset = Ruleset("rules-v1", 1, 1, {"unpaid_policy": "allow"})
    governance.add_ruleset(initial_ruleset, occurred_at=CREATED_AT)
    create_exception_proposal(governance)
    assert decide(governance, "exception-proposal") is ProposalStatus.APPROVED
    governance.create_rotation_proposal(
        proposal_id="rotation-proposal",
        title="New base order",
        description="Reverse the base order.",
        proposer_id="member-a",
        rotation_order=tuple(reversed(MEMBERS)),
        approval_threshold=Decimal("60"),
        effective_cycle=4,
        current_cycle=1,
        created_at=CREATED_AT,
        voting_deadline=DEADLINE,
    )
    assert decide(governance, "rotation-proposal") is ProposalStatus.APPROVED
    ruleset = Ruleset("rules-v2", 2, 5, {"unpaid_policy": "allow"})
    create_ruleset_proposal(governance, "rules-proposal", ruleset)
    assert decide(governance, "rules-proposal") is ProposalStatus.APPROVED
    governance.create_rotation_proposal(
        proposal_id="open-proposal",
        title="Pending base order",
        description="Preserve this open proposal across a snapshot.",
        proposer_id="member-a",
        rotation_order=MEMBERS,
        approval_threshold=Decimal("60"),
        effective_cycle=6,
        current_cycle=1,
        created_at=CREATED_AT,
        voting_deadline=DEADLINE,
    )
    governance.open_proposal("open-proposal", occurred_at=OPENED_AT)
    governance.vote(
        "open-proposal",
        "member-a",
        VoteChoice.YES,
        occurred_at=VOTED_AT,
    )

    snapshot = governance.snapshot()
    restored = GovernanceRegistry.from_snapshot(snapshot)

    assert isinstance(snapshot, GovernanceSnapshot)
    assert restored.snapshot() == snapshot
    assert restored.resolve_rotation_for_cycle(2).recipient_id == "member-e"
    assert restored.rotation_for_cycle(4).member_ids == tuple(reversed(MEMBERS))
    assert restored.ruleset_for_cycle(5) == ruleset
    restored_open_proposal = next(
        item
        for item in restored.snapshot().proposals
        if item.proposal_id == "open-proposal"
    )
    assert restored_open_proposal.votes == (("member-a", VoteChoice.YES),)
    assert tuple(event.event_id for event in restored.snapshot().audit_events) == tuple(
        event.event_id for event in snapshot.audit_events
    )


def test_snapshot_values_are_immutable_and_detached_from_live_proposals() -> None:
    governance = registry()
    proposal = create_exception_proposal(governance)
    snapshot = governance.snapshot()

    proposal.status = ProposalStatus.REJECTED
    proposal.votes["member-a"] = VoteChoice.NO
    saved_proposal = snapshot.proposals[0]

    assert saved_proposal.status is ProposalStatus.DRAFT
    assert saved_proposal.votes == ()
    with pytest.raises(AttributeError):
        saved_proposal.status = ProposalStatus.APPROVED


def test_snapshot_preserves_shared_audit_history_without_claiming_external_events() -> (
    None
):
    audit_registry = AuditEventRegistry()
    external_event = audit_registry.record(
        event_id="external:1",
        event_type="external_record",
        aggregate_type="external",
        aggregate_id="external-aggregate",
        occurred_at=CREATED_AT,
        actor_id=None,
        source_event=None,
        details={"source": "another capability"},
    )
    governance = GovernanceRegistry(
        MEMBERS,
        ClassicRotation.from_active_members(MEMBERS),
        audit_registry=audit_registry,
    )
    create_exception_proposal(governance)

    snapshot = governance.snapshot()
    restored = GovernanceRegistry.from_snapshot(snapshot)

    assert snapshot.audit_events[0] == external_event
    assert snapshot.governance_event_ids == ("proposal_created:exception-proposal:2",)
    assert restored.snapshot() == snapshot


def test_snapshot_rejects_unsupported_schema_and_inconsistent_effect_state() -> None:
    governance = registry()
    create_exception_proposal(governance)
    assert decide(governance, "exception-proposal") is ProposalStatus.APPROVED
    snapshot = governance.snapshot()

    with pytest.raises(ValueError, match="Unsupported governance snapshot schema"):
        GovernanceRegistry.from_snapshot(replace(snapshot, schema_version=2))
    incomplete = replace(snapshot, rotation_exceptions=())
    with pytest.raises(
        ValueError,
        match="rotation exception audit events do not match applied effects",
    ):
        GovernanceRegistry.from_snapshot(incomplete)
