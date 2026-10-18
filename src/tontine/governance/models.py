"""Immutable governance values and proposal lifecycle records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from tontine._datetime import require_aware_datetime
from tontine.classic import ClassicRotation


class ProposalStatus(StrEnum):
    """Lifecycle states for governance proposals."""

    DRAFT = "draft"
    OPEN = "open"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class VoteChoice(StrEnum):
    """Supported one-member-one-vote choices."""

    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"


def _freeze_rule_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze_rule_value(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze_rule_value(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze_rule_value(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze_rule_value(item) for item in value)
    if isinstance(value, frozenset):
        return frozenset(_freeze_rule_value(item) for item in value)
    return value


@dataclass(frozen=True)
class Ruleset:
    """Immutable version of group rules effective from a cycle onward."""

    ruleset_id: str
    version: int
    effective_cycle: int
    rules: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.ruleset_id.strip():
            raise ValueError("Ruleset identifier is required.")
        if self.version < 1 or self.effective_cycle < 1:
            raise ValueError("Ruleset version and effective cycle must be positive.")
        object.__setattr__(self, "rules", _freeze_rule_value(self.rules))


@dataclass(frozen=True)
class RotationOrderEffect:
    """Approved change to the base recipient order from an effective cycle."""

    rotation: ClassicRotation
    effective_cycle: int

    def __post_init__(self) -> None:
        if self.effective_cycle < 1:
            raise ValueError("Rotation effect cycle must be positive.")
        ClassicRotation.from_active_members(self.rotation.member_ids)


@dataclass(frozen=True)
class RotationExceptionEffect:
    """Approved change to the recipient for one cycle only."""

    exception_id: str
    recipient_id: str
    cycle_number: int

    def __post_init__(self) -> None:
        if not self.exception_id.strip() or not self.recipient_id.strip():
            raise ValueError("Rotation exception identity and recipient are required.")
        if self.cycle_number < 1:
            raise ValueError("Rotation exception cycle must be positive.")


@dataclass(frozen=True)
class RulesetActivationEffect:
    """Approved activation of an immutable ruleset."""

    ruleset: Ruleset


ProposalEffect = RotationOrderEffect | RotationExceptionEffect | RulesetActivationEffect


@dataclass(frozen=True)
class ProposalTally:
    """Auditable vote and approval counts for one proposal evaluation."""

    eligible_count: int
    yes_count: int
    no_count: int
    abstain_count: int
    non_voting_count: int
    quorum_required: int
    quorum_met: bool
    yes_percentage: Decimal
    approval_threshold: Decimal
    threshold_met: bool
    approved: bool

    @property
    def participation_count(self) -> int:
        """Return the number of members who cast any vote."""
        return self.eligible_count - self.non_voting_count


@dataclass(frozen=True)
class ProposalEvaluation:
    """Immutable proposal status and tally at an explicit evaluation time."""

    status: ProposalStatus
    evaluated_at: datetime
    tally: ProposalTally

    def __post_init__(self) -> None:
        require_aware_datetime(self.evaluated_at, "evaluated_at")


@dataclass
class RotationProposal:
    """A voteable rotation change with a frozen electorate and approval policy.

    ``created_at``, ``voting_deadline``, and ``opened_at`` must be timezone-aware.
    Abstentions count toward quorum but not toward yes votes.
    """

    proposal_id: str
    title: str
    description: str
    proposer_id: str
    rotation_order: tuple[str, ...]
    approval_threshold: Decimal
    effective_cycle: int
    created_at: datetime
    voting_deadline: datetime
    status: ProposalStatus = ProposalStatus.DRAFT
    votes: dict[str, VoteChoice] = field(default_factory=dict)
    eligible_member_ids: tuple[str, ...] = ()
    current_cycle: int | None = None
    quorum_numerator: int = 2
    quorum_denominator: int = 3
    opened_at: datetime | None = None
    evaluation: ProposalEvaluation | None = None
    effect: ProposalEffect | None = None

    def __post_init__(self) -> None:
        for value, label in (
            (self.proposal_id, "Proposal identifier"),
            (self.title, "Proposal title"),
            (self.description, "Proposal description"),
            (self.proposer_id, "Proposal proposer"),
        ):
            if not value.strip():
                raise ValueError(f"{label} is required.")
        require_aware_datetime(self.created_at, "created_at")
        require_aware_datetime(self.voting_deadline, "voting_deadline")
        if self.voting_deadline < self.created_at:
            raise ValueError("Proposal deadline cannot precede creation.")
        if self.effective_cycle < 1 or (
            self.current_cycle is not None
            and (self.current_cycle < 1 or self.effective_cycle <= self.current_cycle)
        ):
            raise ValueError("Proposal effective cycle must be strictly future.")
        if not self.approval_threshold.is_finite() or not Decimal(
            "0"
        ) < self.approval_threshold <= Decimal("100"):
            raise ValueError(
                "Approval threshold must be greater than 0 and at most 100."
            )
        if (
            self.quorum_denominator < 1
            or not 0 <= self.quorum_numerator <= self.quorum_denominator
        ):
            raise ValueError("Proposal quorum must be a fraction from 0 to 1.")
        if self.rotation_order:
            object.__setattr__(
                self,
                "rotation_order",
                ClassicRotation.from_active_members(self.rotation_order).member_ids,
            )
        effect = self.effect
        if effect is None and self.rotation_order:
            effect = RotationOrderEffect(
                ClassicRotation.from_active_members(self.rotation_order),
                self.effective_cycle,
            )
            self.effect = effect
        if effect is None:
            raise ValueError("Proposal must define a typed decision effect.")
        if isinstance(effect, RotationOrderEffect):
            if (
                effect.effective_cycle != self.effective_cycle
                or effect.rotation.member_ids != self.rotation_order
            ):
                raise ValueError("Rotation proposal effect does not match its context.")
        elif isinstance(effect, RotationExceptionEffect):
            if effect.cycle_number != self.effective_cycle or self.rotation_order:
                raise ValueError(
                    "Rotation exception effect does not match its context."
                )
        elif isinstance(effect, RulesetActivationEffect):
            if (
                effect.ruleset.effective_cycle != self.effective_cycle
                or self.rotation_order
            ):
                raise ValueError("Ruleset effect does not match its context.")
        else:
            raise TypeError(
                "Proposal effect must be a supported typed decision effect."
            )
        eligible = tuple(self.eligible_member_ids)
        if any(not member_id.strip() for member_id in eligible):
            raise ValueError("Proposal electorate member IDs must be non-empty.")
        if len(set(eligible)) != len(eligible):
            raise ValueError("Proposal electorate member IDs must be unique.")
        object.__setattr__(self, "eligible_member_ids", tuple(sorted(eligible)))
        if self.opened_at is not None:
            require_aware_datetime(self.opened_at, "opened_at")
            if not self.created_at <= self.opened_at <= self.voting_deadline:
                raise ValueError("Proposal open time must be within its lifecycle.")
        self.status = ProposalStatus(self.status)
        self.votes = {
            member_id: VoteChoice(choice) for member_id, choice in self.votes.items()
        }
        if self.eligible_member_ids and not set(self.votes).issubset(
            self.eligible_member_ids
        ):
            raise ValueError("Proposal votes must belong to its frozen electorate.")


__all__ = [
    "ProposalEvaluation",
    "ProposalEffect",
    "ProposalStatus",
    "ProposalTally",
    "RotationExceptionEffect",
    "RotationOrderEffect",
    "RotationProposal",
    "Ruleset",
    "RulesetActivationEffect",
    "VoteChoice",
]
