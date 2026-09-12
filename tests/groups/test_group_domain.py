"""Tests for draft tontines and membership validation."""

from __future__ import annotations

import pytest

from tontine.exceptions import (
    DuplicateMemberError,
    InvalidCurrencyError,
    InvalidMembershipTransitionError,
)
from tontine.groups import Group, GroupStatus
from tontine.members import Member, MemberRole, MembershipStatus


def test_create_draft_tontine_with_valid_currency() -> None:
    """A draft tontine may be created only with a valid ISO currency code."""
    group = Group.create_draft(
        group_id="grp-001",
        name="Community Circle",
        base_currency="JPY",
    )

    assert group.group_id == "grp-001"
    assert group.name == "Community Circle"
    assert group.base_currency == "JPY"
    assert group.status is GroupStatus.DRAFT


def test_reject_invalid_currency_code() -> None:
    """Unsupported currency codes are rejected at the domain boundary."""
    with pytest.raises(InvalidCurrencyError):
        Group.create_draft(group_id="grp-002", name="Bad Group", base_currency="XYZ")


def test_add_members_with_unique_identifiers_and_roles() -> None:
    """New members are keyed by identifier and track explicit roles and states."""
    group = Group.create_draft(group_id="grp-003", name="Members", base_currency="JPY")

    member = Member.create(
        member_id="member-001",
        display_name="Alice",
        role=MemberRole.MEMBER,
    )
    group.add_member(member)

    assert group.members["member-001"].display_name == "Alice"
    assert group.members["member-001"].role is MemberRole.MEMBER
    assert group.members["member-001"].status is MembershipStatus.INVITED


def test_reject_duplicate_member_identifiers() -> None:
    """Duplicate member IDs are rejected to preserve identity integrity."""
    group = Group.create_draft(group_id="grp-004", name="Dupes", base_currency="JPY")
    group.add_member(Member.create("member-001", "Alice", MemberRole.MEMBER))

    with pytest.raises(DuplicateMemberError):
        group.add_member(
            Member.create(
                "member-001",
                "Alice Duplicate",
                MemberRole.MEMBER,
            )
        )


def test_member_status_transitions_are_valid() -> None:
    """Membership status transitions must follow the approved lifecycle."""
    member = Member.create("member-002", "Bob", MemberRole.TREASURER)

    member.activate()
    assert member.status is MembershipStatus.ACTIVE

    member.suspend()
    assert member.status is MembershipStatus.SUSPENDED

    member.activate()
    assert member.status is MembershipStatus.ACTIVE

    member.leave()
    assert member.status is MembershipStatus.LEFT

    with pytest.raises(InvalidMembershipTransitionError):
        member.activate()
