"""Classic tontine rotation and payout calculation primitives."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from hashlib import sha256
from typing import TYPE_CHECKING

from tontine._datetime import require_aware_datetime
from tontine.currencies import CurrencyCode
from tontine.exceptions import DuplicatePayoutError

from .rotation_schedule import (
    ApprovedRotationException,
    ClassicRotationResolution,
    ClassicRotationSchedule,
    ClassicRotationVersion,
)

if TYPE_CHECKING:
    from tontine.members import ParticipationShare

_RANDOMIZATION_ALGORITHM_VERSION = "sha256-fisher-yates-v1"
_RANDOMIZATION_DOMAIN = b"tontine-core/classic-rotation/sha256-fisher-yates-v1\0"
_UINT64_RANGE = 1 << 64


def _decimal_amount(value: Decimal | int | str) -> Decimal:
    if not isinstance(value, (Decimal, int, str)) or isinstance(value, float):
        raise TypeError("Payout amounts must use Decimal-compatible values.")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Payout amount must be a valid decimal.") from exc
    if not amount.is_finite():
        raise ValueError("Payout amount must be finite.")
    if amount < 0:
        raise ValueError("Payout amount must be non-negative.")
    return amount


def _seeded_order(active_member_ids: tuple[str, ...], seed: str) -> tuple[str, ...]:
    """Return a stable Fisher-Yates shuffle independent of Python's RNG version."""
    ordered_ids = list(active_member_ids)
    seed_bytes = _RANDOMIZATION_DOMAIN + seed.encode("utf-8")
    counter = 0
    for index in range(len(ordered_ids) - 1, 0, -1):
        bound = index + 1
        acceptance_limit = _UINT64_RANGE - (_UINT64_RANGE % bound)
        while True:
            digest = sha256(seed_bytes + counter.to_bytes(8, "big")).digest()
            counter += 1
            candidate = int.from_bytes(digest[:8], "big")
            if candidate < acceptance_limit:
                swap_index = candidate % bound
                break
            # Rejection avoids modulo bias while keeping the mapping versioned.
        ordered_ids[index], ordered_ids[swap_index] = (
            ordered_ids[swap_index],
            ordered_ids[index],
        )
    return tuple(ordered_ids)


@dataclass(frozen=True)
class RotationRandomizationProvenance:
    """Immutable inputs and audit context for one generated rotation order.

    ``occurred_at`` must be timezone-aware; construct it with
    ``datetime.timezone.utc`` or ``zoneinfo.ZoneInfo``.
    """

    seed: str
    algorithm_version: str
    active_member_ids: tuple[str, ...]
    generated_order: tuple[str, ...]
    actor_id: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        if not self.seed.strip():
            raise ValueError("Rotation randomization seed is required.")
        if self.algorithm_version != _RANDOMIZATION_ALGORITHM_VERSION:
            raise ValueError(
                f"Unsupported rotation randomization algorithm "
                f"{self.algorithm_version!r}."
            )
        if not self.actor_id.strip():
            raise ValueError("Rotation randomization actor is required.")
        require_aware_datetime(self.occurred_at, "occurred_at")
        if not self.active_member_ids:
            raise ValueError("At least one active member is required for rotation.")
        if self.active_member_ids != tuple(sorted(self.active_member_ids)):
            raise ValueError("Randomization active members must be in sorted order.")
        if len(set(self.active_member_ids)) != len(self.active_member_ids):
            raise ValueError("Rotation contains duplicate active members.")
        if any(not member_id.strip() for member_id in self.active_member_ids):
            raise ValueError("Rotation member identifiers must be non-empty.")
        if (
            len(self.generated_order) != len(self.active_member_ids)
            or set(self.generated_order) != set(self.active_member_ids)
        ):
            raise ValueError(
                "Generated rotation order must contain each active member once."
            )

    def reconstruct(self) -> ClassicRotation:
        """Rebuild and verify the recorded rotation from its seed and algorithm.

        Returns:
            The immutable rotation produced by the recorded inputs.

        Raises:
            ValueError: If the recorded order does not match its provenance.
        """
        expected_order = _seeded_order(self.active_member_ids, self.seed)
        if expected_order != self.generated_order:
            raise ValueError(
                "Recorded rotation order does not match its randomization provenance."
            )
        return ClassicRotation(self.generated_order, randomization=self)


@dataclass(frozen=True)
class ClassicRotation:
    """Deterministic recipient order for a classic tontine.

    When created by :meth:`randomized`, ``randomization`` carries the immutable
    seed, algorithm version, input member set, actor, and occurrence time.
    """

    member_ids: tuple[str, ...]
    randomization: RotationRandomizationProvenance | None = None

    @classmethod
    def from_active_members(
        cls,
        active_member_ids: tuple[str, ...],
    ) -> ClassicRotation:
        """Create a rotation from the current active member order.

        Args:
            active_member_ids: Ordered, unique active member identifiers.

        Returns:
            A deterministic immutable rotation.

        Raises:
            ValueError: If the order is empty, duplicated, or contains blanks.
        """
        if not active_member_ids:
            raise ValueError("At least one active members is required for rotation.")
        if any(not member_id.strip() for member_id in active_member_ids):
            raise ValueError("Rotation member identifiers must be non-empty.")
        if len(set(active_member_ids)) != len(active_member_ids):
            raise ValueError("Rotation contains duplicate active members.")
        return cls(tuple(active_member_ids))

    @classmethod
    def from_active_shares(
        cls,
        shares: Iterable[ParticipationShare],
        cycle_number: int,
    ) -> ClassicRotation:
        """Create a rotation from shares active in the supplied cycle.

        Args:
            shares: Ordered share records whose IDs form the rotation positions.
            cycle_number: One-based cycle for which all shares must be active.

        Raises:
            ValueError: If any share is inactive or the resulting IDs are invalid.
        """
        active_shares = tuple(shares)
        if any(not share.is_active_for(cycle_number) for share in active_shares):
            raise ValueError("Rotation shares must be active in the specified cycle.")
        return cls.from_active_members(
            tuple(str(share.share_id) for share in active_shares)
        )

    @classmethod
    def randomized(
        cls,
        active_member_ids: tuple[str, ...],
        seed: str,
        actor_id: str,
        occurred_at: datetime,
    ) -> ClassicRotation:
        """Generate one reproducible order and retain its audit provenance.

        The active member set is sorted before shuffling so the same seed and
        members produce the same order regardless of input iteration order.
        The versioned SHA-256 Fisher-Yates algorithm is implemented here rather
        than delegated to Python's version-dependent ``random`` module.

        Args:
            active_member_ids: Unique active member identifiers to randomize.
            seed: Non-empty, caller-supplied UTF-8 seed.
            actor_id: Non-empty identifier of the actor initiating randomization.
            occurred_at: Timezone-aware randomization occurrence timestamp.

        Returns:
            An immutable rotation carrying its randomization provenance.

        Raises:
            ValueError: If member identifiers, seed, actor, or timestamp is
                invalid.
        """
        canonical_members = cls.from_active_members(
            tuple(sorted(active_member_ids))
        ).member_ids
        generated_order = _seeded_order(canonical_members, seed)
        provenance = RotationRandomizationProvenance(
            seed=seed,
            algorithm_version=_RANDOMIZATION_ALGORITHM_VERSION,
            active_member_ids=canonical_members,
            generated_order=generated_order,
            actor_id=actor_id,
            occurred_at=occurred_at,
        )
        return cls(generated_order, randomization=provenance)

    @classmethod
    def from_randomization(
        cls,
        provenance: RotationRandomizationProvenance,
    ) -> ClassicRotation:
        """Reconstruct a rotation and verify its stored provenance.

        Args:
            provenance: Recorded seed, algorithm version, member set, order,
                actor, and occurrence time.

        Returns:
            The reconstructed immutable rotation.

        Raises:
            ValueError: If the algorithm is unsupported or the recorded order
                does not match its provenance.
        """
        return provenance.reconstruct()

    def recipient_for_cycle(self, cycle_number: int) -> str:
        """Return the recipient for a one-based cycle number.

        Args:
            cycle_number: Positive cycle number; values wrap at the end.

        Returns:
            The member ID selected for the cycle.
        """
        if cycle_number < 1:
            raise ValueError("Cycle number must be positive.")
        return self.member_ids[(cycle_number - 1) % len(self.member_ids)]

    def expected_payout(
        self,
        contributions: dict[str, Decimal | int | str],
    ) -> Decimal:
        """Return the exact Decimal sum of contributions for the rotation.

        Args:
            contributions: Decimal-compatible amounts keyed by every member ID.

        Returns:
            The exact unquantized Decimal contribution pool.
        """
        if set(contributions) != set(self.member_ids):
            raise ValueError("Contributors must match the active rotation members.")
        return sum(
            (_decimal_amount(amount) for amount in contributions.values()),
            Decimal("0"),
        )


class UnpaidContributionPolicy(StrEnum):
    """Whether a classic payout may proceed with outstanding contributions."""

    ALLOW = "allow"
    DENY = "deny"


def can_pay_out(
    outstanding_amount: Decimal | int | str,
    policy: UnpaidContributionPolicy | str | None,
) -> bool:
    """Evaluate payout eligibility using an explicit unpaid policy."""
    outstanding = _decimal_amount(outstanding_amount)
    if outstanding == 0:
        return True
    if policy is None:
        raise ValueError("An unpaid-contribution policy is required.")
    return UnpaidContributionPolicy(policy) is UnpaidContributionPolicy.ALLOW


@dataclass(frozen=True)
class ClassicPayout:
    """Immutable record of a classic cycle payout decision.

    ``recorded_at`` must be timezone-aware; construct it with
    ``datetime.timezone.utc`` or ``zoneinfo.ZoneInfo``.
    """

    cycle_number: int
    recipient_id: str
    amount: Decimal
    currency: CurrencyCode
    recorded_at: datetime
    source_event: str

    def __post_init__(self) -> None:
        if self.cycle_number < 1:
            raise ValueError("Payout cycle number must be positive.")
        if not self.recipient_id.strip():
            raise ValueError("Payout recipient is required.")
        if not self.source_event.strip():
            raise ValueError("Payout source event is required.")
        require_aware_datetime(self.recorded_at, "recorded_at")
        object.__setattr__(self, "amount", _decimal_amount(self.amount))
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))


class ClassicPayoutRegistry:
    """Store one immutable payout decision for each classic cycle."""

    def __init__(self) -> None:
        self._payouts: dict[int, ClassicPayout] = {}

    def record(
        self,
        cycle_number: int,
        recipient_id: str,
        amount: Decimal | int | str,
        currency: str,
        recorded_at: datetime,
        source_event: str,
    ) -> ClassicPayout:
        """Record a payout with an explicit timezone-aware occurrence time.

        ``recorded_at`` must be aware; construct it with ``datetime.timezone.utc``
        or ``zoneinfo.ZoneInfo``.
        """
        if cycle_number in self._payouts:
            raise DuplicatePayoutError(
                f"Cycle {cycle_number} already has a recorded payout."
            )
        payout = ClassicPayout(
            cycle_number=cycle_number,
            recipient_id=recipient_id,
            amount=_decimal_amount(amount),
            currency=CurrencyCode(currency),
            recorded_at=recorded_at,
            source_event=source_event,
        )
        self._payouts[cycle_number] = payout
        return payout


__all__ = [
    "ApprovedRotationException",
    "ClassicPayout",
    "ClassicPayoutRegistry",
    "ClassicRotation",
    "ClassicRotationResolution",
    "ClassicRotationSchedule",
    "ClassicRotationVersion",
    "RotationRandomizationProvenance",
    "UnpaidContributionPolicy",
    "can_pay_out",
]
