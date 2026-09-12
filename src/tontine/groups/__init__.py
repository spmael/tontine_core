"""Group and membership domain behavior."""

from __future__ import annotations

import re
from enum import StrEnum

from tontine.exceptions import (
    DuplicateGroupError,
    DuplicateMemberError,
    InvalidCurrencyError,
)

from ..members import Member

_VALID_CURRENCY_CODES = {
    "XAF",
    "XOF",
    "NGN",
    "GHS",
    "INR",
    "KES",
    "TZS",
    "UGX",
    "ZAR",
    "JPY",
    "CNY",
    "EUR",
    "GBP",
    "USD",
}


class GroupId(str):
    """Strongly-typed tontine identifier."""

    def __new__(cls, value: str) -> GroupId:
        if not value or not value.strip():
            raise ValueError("Group identifier is required.")
        if any(char.isspace() for char in value):
            raise ValueError("Group identifier cannot contain whitespace.")
        return str.__new__(cls, value)


class CurrencyCode(str):
    """ISO 4217-style currency code value object."""

    def __new__(cls, value: str) -> CurrencyCode:
        if not re.fullmatch(r"[A-Z]{3}", value):
            raise InvalidCurrencyError(f"Invalid currency code: {value!r}.")
        if value not in _VALID_CURRENCY_CODES:
            raise InvalidCurrencyError(f"Unsupported currency code: {value!r}.")
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
    ) -> None:
        self.group_id = GroupId(group_id)
        self.name = name.strip()
        if not self.name:
            raise ValueError("Group name is required.")
        self.base_currency = CurrencyCode(base_currency)
        self.status = status
        self.members: dict[str, Member] = {}

    @classmethod
    def create_draft(
        cls,
        group_id: str,
        name: str,
        base_currency: str,
    ) -> Group:
        """Create a new tontine in draft status with valid currency metadata."""
        return cls(
            group_id=GroupId(group_id),
            name=name,
            base_currency=CurrencyCode(base_currency),
            status=GroupStatus.DRAFT,
        )

    def add_member(self, member: Member) -> None:
        """Attach a member to the group while enforcing unique identifiers."""
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
        """Store a group keyed by its domain identifier."""
        if group.group_id in self._groups:
            raise DuplicateGroupError(
                f"Group {group.group_id!r} is already registered in the repository."
            )
        self._groups[group.group_id] = group

    def get_group(self, group_id: str) -> Group:
        """Fetch a group by its identifier."""
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
    "CurrencyCode",
    "Group",
    "GroupId",
    "GroupRepository",
    "GroupStatus",
]
