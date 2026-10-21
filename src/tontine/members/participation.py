"""Stable participation shares and their effective-cycle lifecycle."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from decimal import Decimal

from tontine.currencies import CurrencyCode

from .identity import MemberId


def _cycle_number(value: int, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{label} must be a positive cycle number.")
    return value


class ParticipationShareId(str):
    """Stable identifier for one participation share."""

    def __new__(cls, value: str) -> ParticipationShareId:
        if not value or not value.strip():
            raise ValueError("Participation share identifier is required.")
        if any(char.isspace() for char in value):
            raise ValueError(
                "Participation share identifier cannot contain whitespace."
            )
        return str.__new__(cls, value)


@dataclass(frozen=True, slots=True)
class ParticipationShare:
    """A distinct share owned by one member for an effective-cycle interval.

    A share is active from ``effective_cycle`` through the cycle immediately
    before ``retired_from_cycle``. Rotation versions remain independent,
    immutable records and are not rewritten when a share is retired.
    """

    share_id: ParticipationShareId | str
    member_id: MemberId | str
    effective_cycle: int
    retired_from_cycle: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "share_id", ParticipationShareId(self.share_id))
        object.__setattr__(self, "member_id", MemberId(self.member_id))
        _cycle_number(self.effective_cycle, "Effective cycle")
        if self.retired_from_cycle is not None:
            _cycle_number(self.retired_from_cycle, "Retirement cycle")
            if self.retired_from_cycle <= self.effective_cycle:
                raise ValueError("Retirement cycle must follow the effective cycle.")

    def is_active_for(self, cycle_number: int) -> bool:
        """Return whether the share participates in a one-based cycle."""
        cycle = _cycle_number(cycle_number, "Cycle")
        return self.effective_cycle <= cycle and (
            self.retired_from_cycle is None or cycle < self.retired_from_cycle
        )


class ParticipationShareRegistry:
    """Register stable shares and resolve their ownership by effective cycle."""

    def __init__(self) -> None:
        self._shares: dict[ParticipationShareId, ParticipationShare] = {}

    def register(self, share: ParticipationShare) -> None:
        """Register a share, rejecting duplicate stable identifiers.

        Args:
            share: Immutable share record with a valid member identifier.

        Raises:
            ValueError: If the share identifier already exists.
        """
        if share.share_id in self._shares:
            raise ValueError(f"Participation share {share.share_id!r} already exists.")
        self._shares[ParticipationShareId(share.share_id)] = share

    def retire(self, share_id: str, effective_cycle: int) -> ParticipationShare:
        """Set the cycle from which a registered share is no longer active.

        Args:
            share_id: Stable identifier of the share to retire.
            effective_cycle: First one-based cycle in which it is inactive.

        Returns:
            The replacement immutable share record.

        Raises:
            KeyError: If the share is not registered.
            ValueError: If the share was already retired or the cycle is invalid.
        """
        identifier = ParticipationShareId(share_id)
        share = self._shares[identifier]
        retirement_cycle = _cycle_number(effective_cycle, "Retirement cycle")
        if share.retired_from_cycle is not None:
            raise ValueError(f"Participation share {identifier!r} is already retired.")
        if retirement_cycle <= share.effective_cycle:
            raise ValueError("Retirement cycle must follow the effective cycle.")
        retired = replace(share, retired_from_cycle=retirement_cycle)
        self._shares[identifier] = retired
        return retired

    def get(self, share_id: str) -> ParticipationShare:
        """Return a registered share by its stable identifier."""
        return self._shares[ParticipationShareId(share_id)]

    def shares_for_member(self, member_id: str) -> tuple[ParticipationShare, ...]:
        """Return a member's shares in stable identifier order."""
        identifier = MemberId(member_id)
        return tuple(
            share
            for share in sorted(self._shares.values(), key=lambda item: item.share_id)
            if share.member_id == identifier
        )

    def shares_for_cycle(self, cycle_number: int) -> tuple[ParticipationShare, ...]:
        """Return shares active in a cycle, ordered by stable identifier."""
        cycle = _cycle_number(cycle_number, "Cycle")
        return tuple(
            share
            for share in sorted(self._shares.values(), key=lambda item: item.share_id)
            if share.is_active_for(cycle)
        )

    def member_for_share(self, share_id: str, cycle_number: int) -> MemberId:
        """Resolve the owning member for a share active in the specified cycle.

        Raises:
            KeyError: If the share is not registered.
            ValueError: If the share is not active in the specified cycle.
        """
        share = self.get(share_id)
        if not share.is_active_for(cycle_number):
            raise ValueError(
                f"Participation share {share.share_id!r} is not active in cycle "
                f"{cycle_number}."
            )
        return MemberId(share.member_id)

    def roll_up_amounts(
        self,
        amounts_by_share: Mapping[str, Decimal],
        cycle_number: int,
        currency: str,
    ) -> dict[tuple[MemberId, CurrencyCode], Decimal]:
        """Aggregate same-currency share amounts by owning member.

        Args:
            amounts_by_share: Exact Decimal amounts keyed by stable share ID.
            cycle_number: Cycle whose active shares are being reported.
            currency: ISO 4217 currency code shared by all supplied amounts.

        Returns:
            Exact Decimal totals keyed by member and currency. The aggregation
            applies ``member_total = sum(active_share_amounts)`` without
            conversion or rounding.

        Raises:
            KeyError: If an amount references an unknown share.
            TypeError: If an amount is not a Decimal.
            ValueError: If a share is inactive or an amount is non-finite.
        """
        reporting_currency = CurrencyCode(currency)
        totals: dict[tuple[MemberId, CurrencyCode], Decimal] = {}
        for share_id, amount in sorted(amounts_by_share.items()):
            if not isinstance(amount, Decimal):
                raise TypeError("Share amounts must be Decimal values.")
            if not amount.is_finite():
                raise ValueError("Share amounts must be finite.")
            member_id = self.member_for_share(share_id, cycle_number)
            key = (member_id, reporting_currency)
            totals[key] = totals.get(key, Decimal("0")) + amount
        return totals


__all__ = [
    "ParticipationShare",
    "ParticipationShareId",
    "ParticipationShareRegistry",
]
