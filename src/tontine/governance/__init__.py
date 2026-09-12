"""Framework-independent governance proposals, votes, rulesets, and audit events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from tontine.audit import AuditEvent, AuditEventRegistry
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


@dataclass(frozen=True)
class Ruleset:
    """Immutable version of group rules effective from a cycle onward."""

    ruleset_id: str
    version: int
    effective_cycle: int
    rules: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.ruleset_id.strip():
            raise ValueError("Ruleset identifier is required.")
        if self.version < 1 or self.effective_cycle < 1:
            raise ValueError("Ruleset version and effective cycle must be positive.")
        object.__setattr__(self, "rules", dict(self.rules))


@dataclass
class RotationProposal:
    """A voteable rotation change with immutable candidate order and provenance."""

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


class GovernanceRegistry:
    """Manage governance proposals, votes, effective rotations, and audit events."""

    def __init__(
        self,
        active_member_ids: tuple[str, ...],
        initial_rotation: ClassicRotation,
        audit_registry: AuditEventRegistry | None = None,
    ) -> None:
        if not active_member_ids:
            raise ValueError("Governance requires active members.")
        self._active_members = frozenset(active_member_ids)
        self._rotations: dict[int, ClassicRotation] = {1: initial_rotation}
        self._proposals: dict[str, RotationProposal] = {}
        self._rulesets: list[Ruleset] = []
        self._audit_registry = audit_registry or AuditEventRegistry()

    def create_rotation_proposal(
        self,
        proposal_id: str,
        title: str,
        description: str,
        proposer_id: str,
        rotation_order: tuple[str, ...],
        approval_threshold: Decimal,
        effective_cycle: int,
        created_at: datetime,
        voting_deadline: datetime,
    ) -> RotationProposal:
        """Create a draft rotation proposal without changing active history.

        Args:
            proposal_id: Unique proposal identifier.
            title: Short proposal title.
            description: Decision context presented to voters.
            proposer_id: Eligible member creating the proposal.
            rotation_order: Candidate order containing every active member once.
            approval_threshold: Required yes-vote percentage from 0 to 100.
            effective_cycle: First cycle using the approved order.
            created_at: Timezone-aware proposal creation timestamp.
            voting_deadline: Timezone-aware deadline after creation.

        Returns:
            A draft rotation proposal.

        Raises:
            ValueError: If identity, threshold, dates, or rotation order is invalid.
        """
        if proposal_id in self._proposals:
            raise ValueError(f"Proposal {proposal_id!r} already exists.")
        if proposer_id not in self._active_members:
            raise ValueError("Proposal proposer must be an eligible member.")
        if created_at.tzinfo is None or created_at.utcoffset() is None:
            raise ValueError("Proposal timestamps must be timezone-aware.")
        if voting_deadline.tzinfo is None or voting_deadline.utcoffset() is None:
            raise ValueError("Proposal timestamps must be timezone-aware.")
        if not Decimal("0") < approval_threshold <= Decimal("100"):
            raise ValueError(
                "Approval threshold must be greater than 0 and at most 100."
            )
        if effective_cycle < 1 or voting_deadline < created_at:
            raise ValueError("Proposal cycle and dates are invalid.")
        rotation = ClassicRotation.from_active_members(rotation_order)
        if set(rotation.member_ids) != self._active_members:
            raise ValueError("Proposed rotation must contain all active members.")
        proposal = RotationProposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            proposer_id=proposer_id,
            rotation_order=rotation.member_ids,
            approval_threshold=approval_threshold,
            effective_cycle=effective_cycle,
            created_at=created_at,
            voting_deadline=voting_deadline,
        )
        self._proposals[proposal_id] = proposal
        self._audit("proposal_created", proposal_id, created_at)
        return proposal

    def open_proposal(self, proposal_id: str) -> None:
        """Open a draft proposal for voting."""
        proposal = self._proposal(proposal_id)
        if proposal.status is not ProposalStatus.DRAFT:
            raise ValueError("Only draft proposals can be opened.")
        proposal.status = ProposalStatus.OPEN
        self._audit("proposal_opened", proposal_id, proposal.created_at)

    def vote(self, proposal_id: str, member_id: str, choice: VoteChoice) -> None:
        """Record one eligible member vote on an open proposal.

        Args:
            proposal_id: Proposal receiving the vote.
            member_id: Eligible member submitting the vote.
            choice: Yes, no, or abstain.

        Raises:
            ValueError: If the proposal is not open, the member is ineligible,
                or the member has already voted.
        """
        proposal = self._proposal(proposal_id)
        if proposal.status is not ProposalStatus.OPEN:
            raise ValueError("Only open proposals can receive votes.")
        if member_id not in self._active_members:
            raise ValueError("Voter must be an eligible member.")
        if member_id in proposal.votes:
            raise ValueError(f"Member {member_id!r} has already voted.")
        proposal.votes[member_id] = VoteChoice(choice)
        self._audit("vote_submitted", proposal_id, datetime.now().astimezone())

    def evaluate(self, proposal_id: str) -> ProposalStatus:
        """Evaluate approval using yes votes divided by eligible members.

        Args:
            proposal_id: Proposal to evaluate.

        Returns:
            The proposal's resulting status. Approved rotations become effective
            only at their configured cycle.
        """
        proposal = self._proposal(proposal_id)
        if proposal.status is not ProposalStatus.OPEN:
            return proposal.status
        yes_percentage = (
            Decimal(sum(choice is VoteChoice.YES for choice in proposal.votes.values()))
            / Decimal(len(self._active_members))
            * Decimal("100")
        )
        proposal.status = (
            ProposalStatus.APPROVED
            if yes_percentage >= proposal.approval_threshold
            else ProposalStatus.REJECTED
        )
        self._audit("proposal_evaluated", proposal_id, datetime.now().astimezone())
        if proposal.status is ProposalStatus.APPROVED:
            self._rotations[proposal.effective_cycle] = (
                ClassicRotation.from_active_members(proposal.rotation_order)
            )
            self._audit("rotation_approved", proposal_id, datetime.now().astimezone())
        return proposal.status

    def rotation_for_cycle(self, cycle_number: int) -> ClassicRotation:
        """Return the latest approved rotation effective for a cycle."""
        applicable = [cycle for cycle in self._rotations if cycle <= cycle_number]
        if not applicable:
            raise ValueError("Cycle number must be positive.")
        return self._rotations[max(applicable)]

    def audit_events(self, aggregate_id: str) -> tuple[AuditEvent, ...]:
        """Return immutable audit events for a proposal or governance aggregate."""
        return self._audit_registry.events_for("proposal", aggregate_id)

    def add_ruleset(self, ruleset: Ruleset) -> None:
        """Add a new immutable ruleset version in effective-cycle order."""
        if any(existing.version == ruleset.version for existing in self._rulesets):
            raise ValueError(f"Ruleset version {ruleset.version} already exists.")
        self._rulesets.append(ruleset)
        self._rulesets.sort(key=lambda item: item.effective_cycle)
        self._audit("ruleset_added", ruleset.ruleset_id, datetime.now().astimezone())

    def ruleset_for_cycle(self, cycle_number: int) -> Ruleset:
        """Return the latest ruleset effective for a cycle."""
        applicable = [
            item for item in self._rulesets if item.effective_cycle <= cycle_number
        ]
        if not applicable:
            raise KeyError(f"No ruleset is effective for cycle {cycle_number}.")
        return applicable[-1]

    def _proposal(self, proposal_id: str) -> RotationProposal:
        try:
            return self._proposals[proposal_id]
        except KeyError as exc:
            raise KeyError(f"Proposal {proposal_id!r} was not found.") from exc

    def _audit(self, event_type: str, aggregate_id: str, occurred_at: datetime) -> None:
        event_number = len(self._audit_registry.all_events()) + 1
        self._audit_registry.record(
            event_id=f"{event_type}:{aggregate_id}:{event_number}",
            event_type=event_type,
            aggregate_type="proposal",
            aggregate_id=aggregate_id,
            occurred_at=occurred_at,
            actor_id=None,
            source_event=None,
            details={"source": "governance"},
        )


__all__ = [
    "AuditEvent",
    "GovernanceRegistry",
    "ProposalStatus",
    "RotationProposal",
    "Ruleset",
    "VoteChoice",
]
