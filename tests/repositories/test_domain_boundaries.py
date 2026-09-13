from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from tontine.audit import AuditEvent
from tontine.classic import ClassicPayout, ClassicRotation
from tontine.governance import RotationProposal, Ruleset
from tontine.members import Member, MemberRole
from tontine.repositories import (
    InMemoryAuditRepository,
    InMemoryClassicRepository,
    InMemoryGovernanceRepository,
    InMemoryMemberRepository,
)


def test_member_repository_has_duplicate_and_ordering_semantics() -> None:
    repository = InMemoryMemberRepository()
    repository.add(Member.create("member-b", "B", MemberRole.MEMBER, date(2027, 1, 1)))
    repository.add(Member.create("member-a", "A", MemberRole.MEMBER, date(2027, 1, 1)))

    assert [member.member_id for member in repository.list()] == [
        "member-a",
        "member-b",
    ]
    with pytest.raises(ValueError, match="already"):
        repository.add(
            Member.create("member-a", "A2", MemberRole.MEMBER, date(2027, 1, 1))
        )


def test_classic_repository_preserves_rotations_and_payout_order() -> None:
    repository = InMemoryClassicRepository()
    repository.save_rotation(
        "rotation-1", ClassicRotation.from_active_members(("a", "b"))
    )
    repository.record_payout(
        ClassicPayout(
            1,
            "a",
            Decimal("100"),
            "JPY",
            datetime(2027, 1, 1, tzinfo=UTC),
            "payout-1",
        )
    )

    assert repository.get_rotation("rotation-1").recipient_for_cycle(1) == "a"
    assert [payout.cycle_number for payout in repository.payouts()] == [1]

    with pytest.raises(ValueError, match="already"):
        repository.save_rotation(
            "rotation-1", ClassicRotation.from_active_members(("a",))
        )
    with pytest.raises(ValueError, match="already"):
        repository.record_payout(
            ClassicPayout(
                1,
                "a",
                Decimal("100"),
                "JPY",
                datetime(2027, 1, 1, tzinfo=UTC),
                "payout-1",
            )
        )
    with pytest.raises(KeyError, match="not found"):
        repository.get_rotation("missing")


def test_governance_and_audit_repositories_store_immutable_records() -> None:
    governance = InMemoryGovernanceRepository()
    proposal = RotationProposal(
        proposal_id="proposal-1",
        title="Change",
        description="Change rotation",
        proposer_id="member-a",
        rotation_order=("member-a", "member-b"),
        approval_threshold=Decimal("60"),
        effective_cycle=2,
        created_at=datetime(2027, 1, 1, tzinfo=UTC),
        voting_deadline=datetime(2027, 1, 2, tzinfo=UTC),
    )
    governance.save_proposal(proposal)
    governance.save_ruleset(Ruleset("rules-1", 1, 1, {"amount": "100"}))

    audit = InMemoryAuditRepository()
    event = AuditEvent(
        "audit-1",
        "vote.submitted",
        "proposal",
        "proposal-1",
        datetime(2027, 1, 1, tzinfo=UTC),
        "member-a",
        "vote-1",
        {"choice": "yes"},
    )
    audit.record(event)

    assert governance.get_proposal("proposal-1") is proposal
    assert audit.events_for("proposal", "proposal-1") == (event,)
    with pytest.raises(ValueError, match="already"):
        audit.record(event)

    with pytest.raises(ValueError, match="already"):
        governance.save_proposal(proposal)
    with pytest.raises(ValueError, match="already"):
        governance.save_ruleset(Ruleset("rules-1", 1, 1, {"amount": "100"}))
    with pytest.raises(KeyError, match="not found"):
        governance.get_proposal("missing")


def test_member_and_audit_repositories_report_missing_records() -> None:
    member_repository = InMemoryMemberRepository()
    with pytest.raises(KeyError, match="not found"):
        member_repository.get("missing")

    audit_repository = InMemoryAuditRepository()
    assert audit_repository.all_events() == ()
    assert audit_repository.events_for("group", "missing") == ()
