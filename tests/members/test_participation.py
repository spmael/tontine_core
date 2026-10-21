"""Tests for stable participation shares."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from tontine.classic import (
    ClassicRotation,
    ClassicRotationSchedule,
    ClassicRotationVersion,
)
from tontine.contributions import ContributionCycle
from tontine.governance import GovernanceRegistry, VoteChoice
from tontine.members import (
    ParticipationShare,
    ParticipationShareId,
    ParticipationShareRegistry,
)


def test_share_is_active_from_inclusive_effective_cycle_until_retirement() -> None:
    registry = ParticipationShareRegistry()
    share = ParticipationShare("share-b", "member-1", effective_cycle=2)
    registry.register(share)

    retired = registry.retire("share-b", effective_cycle=4)

    assert share.retired_from_cycle is None
    assert retired.retired_from_cycle == 4
    assert [item.share_id for item in registry.shares_for_cycle(1)] == []
    assert [item.share_id for item in registry.shares_for_cycle(2)] == ["share-b"]
    assert [item.share_id for item in registry.shares_for_cycle(3)] == ["share-b"]
    assert [item.share_id for item in registry.shares_for_cycle(4)] == []


def test_share_registry_orders_shares_and_resolves_member_by_cycle() -> None:
    registry = ParticipationShareRegistry()
    registry.register(ParticipationShare("share-z", "member-1", 1))
    registry.register(ParticipationShare("share-a", "member-1", 2))

    assert [share.share_id for share in registry.shares_for_member("member-1")] == [
        "share-a",
        "share-z",
    ]
    assert [share.share_id for share in registry.shares_for_cycle(2)] == [
        "share-a",
        "share-z",
    ]
    assert registry.member_for_share("share-a", 2) == "member-1"
    with pytest.raises(ValueError, match="not active"):
        registry.member_for_share("share-a", 1)


def test_duplicate_share_id_is_rejected_without_replacing_original() -> None:
    registry = ParticipationShareRegistry()
    original = ParticipationShare("share-1", "member-1", 1)
    registry.register(original)

    with pytest.raises(ValueError, match="already exists"):
        registry.register(ParticipationShare("share-1", "member-2", 2))

    assert registry.get("share-1") == original


@pytest.mark.parametrize(
    ("share_id", "member_id", "effective_cycle", "retired_from_cycle"),
    [
        (" ", "member-1", 1, None),
        ("share 1", "member-1", 1, None),
        ("share-1", " ", 1, None),
        ("share-1", "member-1", 0, None),
        ("share-1", "member-1", 2, 2),
        ("share-1", "member-1", 3, 2),
    ],
)
def test_invalid_share_record_is_rejected(
    share_id: str,
    member_id: str,
    effective_cycle: int,
    retired_from_cycle: int | None,
) -> None:
    with pytest.raises(ValueError):
        ParticipationShare(
            share_id,
            member_id,
            effective_cycle,
            retired_from_cycle,
        )


def test_retirement_rejects_unknown_duplicate_and_invalid_transitions() -> None:
    registry = ParticipationShareRegistry()
    registry.register(ParticipationShare("share-1", "member-1", 2))

    with pytest.raises(KeyError):
        registry.retire("unknown", 3)
    with pytest.raises(ValueError, match="must follow"):
        registry.retire("share-1", 2)

    registry.retire("share-1", 4)
    with pytest.raises(ValueError, match="already retired"):
        registry.retire("share-1", 5)


def test_participation_share_id_is_a_validated_string_identifier() -> None:
    assert ParticipationShareId("share-1") == "share-1"
    with pytest.raises(ValueError, match="required"):
        ParticipationShareId("")


def test_share_contributions_retain_owner_and_roll_up_per_currency() -> None:
    registry = ParticipationShareRegistry()
    first = ParticipationShare("share-1", "member-1", 1)
    second = ParticipationShare("share-2", "member-1", 1)
    registry.register(first)
    registry.register(second)
    cycle = ContributionCycle(
        "cycle-1",
        start_date=date(2027, 1, 1),
        due_date=date(2027, 1, 31),
        timezone="UTC",
    )
    cycle.add_expected_share_contribution(first, 1, Decimal("10"))
    cycle.add_expected_share_contribution(second, 1, Decimal("20"))

    first_record = cycle.record_share_contribution(
        first,
        1,
        Decimal("10"),
        as_of=datetime(2027, 1, 15, tzinfo=UTC),
    )
    second_record = cycle.record_share_contribution(
        second,
        1,
        Decimal("20"),
        as_of=datetime(2027, 1, 15, tzinfo=UTC),
    )

    assert first_record.share_id == "share-1"
    assert first_record.member_id == "member-1"
    assert first_record.contribution.participant_id == "share-1"
    assert second_record.contribution.participant_id == "share-2"
    assert registry.roll_up_amounts(
        {
            first_record.share_id: first_record.contribution.actual_amount,
            second_record.share_id: second_record.contribution.actual_amount,
        },
        1,
        "XAF",
    ) == {(first_record.member_id, "XAF"): Decimal("30")}


def test_share_contributions_reject_inactive_shares_without_mutation() -> None:
    share = ParticipationShare("share-1", "member-1", 2)
    cycle = ContributionCycle(
        "cycle-1",
        start_date=date(2027, 1, 1),
        due_date=date(2027, 1, 31),
        timezone="UTC",
    )

    with pytest.raises(ValueError, match="not active"):
        cycle.add_expected_share_contribution(share, 1, Decimal("10"))
    with pytest.raises(ValueError, match="not active"):
        cycle.record_share_contribution(share, 1, Decimal("10"))
    assert cycle.expected_contributions == {}
    assert cycle.recorded_contributions == {}


def test_share_amount_roll_up_rejects_unknown_inactive_and_non_decimal_values() -> None:
    registry = ParticipationShareRegistry()
    registry.register(ParticipationShare("share-1", "member-1", 1))
    registry.register(ParticipationShare("share-2", "member-2", 2))

    with pytest.raises(KeyError):
        registry.roll_up_amounts({"unknown": Decimal("1")}, 1, "XAF")
    with pytest.raises(ValueError, match="not active"):
        registry.roll_up_amounts({"share-2": Decimal("1")}, 1, "XAF")
    with pytest.raises(TypeError, match="Decimal"):
        registry.roll_up_amounts({"share-1": 1}, 1, "XAF")  # type: ignore[dict-item]


def test_share_rotations_resolve_owners_without_rewriting_prior_versions() -> None:
    registry = ParticipationShareRegistry()
    first = ParticipationShare("share-1", "member-1", 1)
    second = ParticipationShare("share-2", "member-2", 1)
    registry.register(first)
    registry.register(second)
    original_rotation = ClassicRotation.from_active_shares(
        registry.shares_for_cycle(1),
        1,
    )
    original_version = ClassicRotationVersion(
        1,
        1,
        original_rotation,
        source_event="rotation-approved-1",
    )
    schedule = ClassicRotationSchedule((original_version,))

    registry.retire("share-2", 2)
    future_rotation = ClassicRotation.from_active_shares(
        registry.shares_for_cycle(2),
        2,
    )
    revised = schedule.with_version(
        ClassicRotationVersion(
            2,
            2,
            future_rotation,
            source_event="rotation-approved-2",
        )
    )

    assert original_rotation.member_ids == ("share-1", "share-2")
    assert schedule.versions == (original_version,)
    assert schedule.resolve_member_for_cycle(1, registry) == "member-1"
    assert revised.resolve_member_for_cycle(2, registry) == "member-1"


def test_multiple_shares_do_not_multiply_governance_votes() -> None:
    share_registry = ParticipationShareRegistry()
    share_registry.register(ParticipationShare("share-1", "member-1", 1))
    share_registry.register(ParticipationShare("share-2", "member-1", 1))
    governance = GovernanceRegistry(
        active_member_ids=("member-1", "member-2"),
        initial_rotation=ClassicRotation.from_active_members(("member-1", "member-2")),
    )
    governance.create_rotation_proposal(
        proposal_id="proposal-1",
        title="Share-neutral voting",
        description="Voting remains person-based.",
        proposer_id="member-1",
        rotation_order=("member-2", "member-1"),
        approval_threshold=Decimal("50"),
        effective_cycle=2,
        current_cycle=1,
        created_at=datetime(2027, 1, 1, tzinfo=UTC),
        voting_deadline=datetime(2027, 1, 15, tzinfo=UTC),
    )
    governance.open_proposal(
        "proposal-1",
        occurred_at=datetime(2027, 1, 2, tzinfo=UTC),
    )
    governance.vote(
        "proposal-1",
        "member-1",
        VoteChoice.YES,
        occurred_at=datetime(2027, 1, 3, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="already voted"):
        governance.vote(
            "proposal-1",
            "member-1",
            VoteChoice.NO,
            occurred_at=datetime(2027, 1, 4, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="eligible"):
        governance.vote(
            "proposal-1",
            "share-2",
            VoteChoice.YES,
            occurred_at=datetime(2027, 1, 4, tzinfo=UTC),
        )
    assert len(share_registry.shares_for_member("member-1")) == 2
