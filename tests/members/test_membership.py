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
