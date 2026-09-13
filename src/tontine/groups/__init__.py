"""Group and membership domain behavior."""

from __future__ import annotations

from enum import StrEnum

from tontine.countries import CountryCode
from tontine.currencies import CurrencyCode
from tontine.exceptions import (
    DuplicateGroupError,
    DuplicateMemberError,
)

from ..members import Member


class GroupId(str):
    """Strongly-typed tontine identifier."""

    def __new__(cls, value: str) -> GroupId:
        if not value or not value.strip():
            raise ValueError("Group identifier is required.")
        if any(char.isspace() for char in value):
            raise ValueError("Group identifier cannot contain whitespace.")
        return str.__new__(cls, value)


class GroupStatus(StrEnum):
    """Lifecycle states for a tontine group."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class Group:
    """A tontine group with membership and lifecycle validation."""

    def __init__(
        self,
        group_id: GroupId,
        name: str,
        base_currency: CurrencyCode,
        status: GroupStatus = GroupStatus.DRAFT,
        jurisdiction: CountryCode | None = None,
    ) -> None:
        self.group_id = GroupId(group_id)
        self.name = name.strip()
        if not self.name:
            raise ValueError("Group name is required.")
        self.base_currency = CurrencyCode(base_currency)
        self.status = status
        self.jurisdiction = (
            None if jurisdiction is None else CountryCode(str(jurisdiction))
        )
        self.members: dict[str, Member] = {}

    @classmethod
    def create_draft(
        cls,
        group_id: str,
        name: str,
        base_currency: str,
        jurisdiction: str | None = None,
    ) -> Group:
        """Create a draft group with validated identity and currency metadata.

        Args:
            group_id: Non-empty identifier without whitespace.
            name: Display name for the group.
            base_currency: Supported three-letter currency code.

        Returns:
            A group in ``draft`` status.
        """
        return cls(
            group_id=GroupId(group_id),
            name=name,
            base_currency=CurrencyCode(base_currency),
            status=GroupStatus.DRAFT,
            jurisdiction=(
                None if jurisdiction is None else CountryCode(jurisdiction)
            ),
        )

    def add_member(self, member: Member) -> None:
        """Attach a member while enforcing unique member identifiers.

        Raises:
            DuplicateMemberError: If the member is already attached.
        """
        if member.member_id in self.members:
            raise DuplicateMemberError(
                f"Member {member.member_id!r} is already present in this tontine."
            )
        self.members[member.member_id] = member

    def __repr__(self) -> str:
        return (
            f"Group(group_id={self.group_id!r}, name={self.name!r}, "
            f"base_currency={self.base_currency!r}, status={self.status.value!r})"
        )


class GroupRepository:
    """Simple in-memory repository for tontines and their members."""

    def __init__(self) -> None:
        self._groups: dict[str, Group] = {}

    def add_group(self, group: Group) -> None:
        """Store a group keyed by its domain identifier.

        Raises:
            DuplicateGroupError: If the group identifier is already stored.
        """
        if group.group_id in self._groups:
            raise DuplicateGroupError(
                f"Group {group.group_id!r} is already registered in the repository."
            )
        self._groups[group.group_id] = group

    def get_group(self, group_id: str) -> Group:
        """Fetch a group by its identifier.

        Raises:
            KeyError: If no group has the requested identifier.
        """
        try:
            return self._groups[group_id]
        except KeyError as exc:
            raise KeyError(f"Group {group_id!r} was not found.") from exc

    def add_member(self, group_id: str, member: Member) -> None:
        """Add a member to a registered group using the group identifier."""
        group = self.get_group(group_id)
        group.add_member(member)

    def get_member(self, group_id: str, member_id: str) -> Member:
        """Fetch a member from a specific group."""
        group = self.get_group(group_id)
        try:
            return group.members[member_id]
        except KeyError as exc:
            raise KeyError(
                f"Member {member_id!r} was not found in group {group_id!r}."
            ) from exc

__all__ = [
    "CountryCode",
    "CurrencyCode",
    "Group",
    "GroupId",
    "GroupRepository",
    "GroupStatus",
]
