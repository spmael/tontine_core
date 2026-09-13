"""Tests for typed membership vocabulary and validation."""

from __future__ import annotations

import pytest

from tontine.exceptions import InvalidMembershipTransitionError
from tontine.members import Member, MemberRole, MembershipStatus


def test_member_roles_are_explicit() -> None:
    """Member roles are represented as explicit domain values."""
    member = Member.create("member-010", "Carrie", MemberRole.ADMINISTRATOR)

    assert member.role is MemberRole.ADMINISTRATOR
    assert member.status is MembershipStatus.INVITED


def test_invalid_transition_is_rejected() -> None:
    """Invalid transitions must raise a domain-specific error."""
    member = Member.create("member-011", "Dana", MemberRole.MEMBER)

    with pytest.raises(InvalidMembershipTransitionError):
        member.remove()

    member.activate()
    with pytest.raises(InvalidMembershipTransitionError):
        member.remove()


def test_reject_invalid_member_identity() -> None:
    """Member identifiers and display names must contain usable values."""
    with pytest.raises(ValueError, match="identifier"):
        Member.create(" ", "Dana", MemberRole.MEMBER)

    with pytest.raises(ValueError, match="whitespace"):
        Member.create("member 012", "Dana", MemberRole.MEMBER)

    with pytest.raises(ValueError, match="Display name"):
        Member.create("member-012", " ", MemberRole.MEMBER)

    with pytest.raises(ValueError, match="identifier"):
        Member.create("", "Dana", MemberRole.MEMBER)


def test_invalid_suspend_leave_and_remove_transitions_are_rejected() -> None:
    """Each membership transition enforces its required prior state."""
    invited = Member.create("member-013", "Eva", MemberRole.MEMBER)
    with pytest.raises(InvalidMembershipTransitionError):
        invited.suspend()
    with pytest.raises(InvalidMembershipTransitionError):
        invited.leave()

    active = Member.create("member-014", "Femi", MemberRole.MEMBER)
    active.activate()
    active.leave()
    active.remove()
    with pytest.raises(InvalidMembershipTransitionError):
        active.remove()
