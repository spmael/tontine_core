"""Tests for the in-memory group repository."""

from __future__ import annotations

from datetime import date

import pytest

from tontine.exceptions import DuplicateGroupError
from tontine.groups import Group, GroupRepository
from tontine.members import Member, MemberRole


def test_repository_adds_and_gets_group_by_identifier() -> None:
    """Groups can be stored and fetched by their domain identifier."""
    repo = GroupRepository()
    group = Group.create_draft("grp-100", "Repo Group", "JPY")

    repo.add_group(group)

    assert repo.get_group("grp-100") is group


def test_repository_adds_and_gets_members_by_identifier() -> None:
    """Members are retrievable from a repository keyed by group and member ID."""
    repo = GroupRepository()
    group = Group.create_draft("grp-200", "Member Group", "USD")
    member = Member.create("member-200", "Amina", MemberRole.MEMBER, date(2027, 1, 1))
    repo.add_group(group)

    repo.add_member("grp-200", member)

    assert repo.get_member("grp-200", "member-200") is member


def test_repository_rejects_duplicate_group_identifiers() -> None:
    """A repository cannot store the same group identifier twice."""
    repo = GroupRepository()
    repo.add_group(Group.create_draft("grp-300", "Alpha", "XOF"))

    with pytest.raises(DuplicateGroupError):
        repo.add_group(Group.create_draft("grp-300", "Duplicate", "XOF"))


def test_repository_rejects_missing_groups_and_members() -> None:
    """Repository lookups report missing group and member records clearly."""
    repo = GroupRepository()

    with pytest.raises(KeyError, match="not found"):
        repo.get_group("missing")

    repo.add_group(Group.create_draft("grp-301", "Lookup Group", "XOF"))
    with pytest.raises(KeyError, match="Member"):
        repo.get_member("grp-301", "missing")
