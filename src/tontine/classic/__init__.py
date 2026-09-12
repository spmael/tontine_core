"""Classic tontine rotation and payout calculation primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum

from tontine.currencies import CurrencyCode
from tontine.exceptions import DuplicatePayoutError


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


@dataclass(frozen=True)
class ClassicRotation:
    """Deterministic recipient order for a classic tontine."""

    member_ids: tuple[str, ...]

    @classmethod
    def from_active_members(
        cls,
        active_member_ids: tuple[str, ...],
    ) -> ClassicRotation:
        """Create a rotation from the current active member order."""
        if not active_member_ids:
            raise ValueError("At least one active members is required for rotation.")
        if any(not member_id.strip() for member_id in active_member_ids):
            raise ValueError("Rotation member identifiers must be non-empty.")
        if len(set(active_member_ids)) != len(active_member_ids):
            raise ValueError("Rotation contains duplicate active members.")
        return cls(tuple(active_member_ids))

    def recipient_for_cycle(self, cycle_number: int) -> str:
        """Return the recipient for a one-based cycle number."""
        if cycle_number < 1:
            raise ValueError("Cycle number must be positive.")
        return self.member_ids[(cycle_number - 1) % len(self.member_ids)]

    def expected_payout(
        self,
        contributions: dict[str, Decimal | int | str],
    ) -> Decimal:
        """Return the exact Decimal sum of contributions for the rotation."""
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
    """Immutable record of a classic cycle payout decision."""

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
        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("Payout timestamps must be timezone-aware.")
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
        """Record a payout without initiating or processing payment."""
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
    "ClassicPayout",
    "ClassicPayoutRegistry",
    "ClassicRotation",
    "UnpaidContributionPolicy",
    "can_pay_out",
]
