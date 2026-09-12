"""Member identity, role, and membership-state behavior."""

from __future__ import annotations

from enum import StrEnum

from tontine.exceptions import InvalidMembershipTransitionError


class MemberId(str):
    """Strongly-typed member identifier."""

    def __new__(cls, value: str) -> MemberId:
        if not value or not value.strip():
            raise ValueError("Member identifier is required.")
        if any(char.isspace() for char in value):
            raise ValueError("Member identifier cannot contain whitespace.")
        return str.__new__(cls, value)


class MemberRole(StrEnum):
    """Explicit tontine roles that do not imply application authentication."""

    MEMBER = "member"
    TREASURER = "treasurer"
    ADMINISTRATOR = "administrator"


class MembershipStatus(StrEnum):
    """Valid member lifecycle states inside a tontine group."""

    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LEFT = "left"
    REMOVED = "removed"


class Member:
    """A tontine member with an explicit status lifecycle."""

    def __init__(
        self,
        member_id: str,
        display_name: str,
        role: MemberRole,
        status: MembershipStatus = MembershipStatus.INVITED,
    ) -> None:
        self.member_id = MemberId(member_id)
        self.display_name = display_name.strip()
        if not self.display_name:
            raise ValueError("Display name is required.")
        self.role = role
        self.status = status

    @classmethod
    def create(
        cls,
        member_id: str,
        display_name: str,
        role: MemberRole,
    ) -> Member:
        """Create a member in invited status for later activation.

        Args:
            member_id: Non-empty identifier without whitespace.
            display_name: Human-readable member name.
            role: Explicit role within the tontine.

        Returns:
            A member in ``invited`` status.
        """
        return cls(
            member_id=member_id,
            display_name=display_name,
            role=role,
            status=MembershipStatus.INVITED,
        )

    def activate(self) -> None:
        """Move the member into active participation if the transition is valid."""
        if self.status not in {MembershipStatus.INVITED, MembershipStatus.SUSPENDED}:
            raise InvalidMembershipTransitionError(
                f"Cannot activate a member in {self.status.value!r} status."
            )
        self.status = MembershipStatus.ACTIVE

    def suspend(self) -> None:
        """Suspend an active member while remaining in the tontine."""
        if self.status is not MembershipStatus.ACTIVE:
            raise InvalidMembershipTransitionError(
                f"Cannot suspend a member in {self.status.value!r} status."
            )
        self.status = MembershipStatus.SUSPENDED

    def leave(self) -> None:
        """Mark a member as having left the tontine."""
        if self.status not in {MembershipStatus.ACTIVE, MembershipStatus.SUSPENDED}:
            raise InvalidMembershipTransitionError(
                f"Cannot leave a member in {self.status.value!r} status."
            )
        self.status = MembershipStatus.LEFT

    def remove(self) -> None:
        """Remove a member only after a valid departure has been recorded."""
        if self.status is not MembershipStatus.LEFT:
            raise InvalidMembershipTransitionError(
                f"Cannot remove a member in {self.status.value!r} status."
            )
        self.status = MembershipStatus.REMOVED

    def __repr__(self) -> str:
        return (
            f"Member(member_id={self.member_id!r}, display_name={self.display_name!r}, "
            f"role={self.role.value!r}, status={self.status.value!r})"
        )


__all__ = ["Member", "MemberId", "MemberRole", "MembershipStatus"]
