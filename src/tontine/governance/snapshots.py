"""Versioned immutable snapshots for governance registry persistence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import TYPE_CHECKING

from tontine.audit import AuditEvent, AuditEventRegistry
from tontine.classic import (
    ApprovedRotationException,
    ClassicRotationSchedule,
    ClassicRotationVersion,
)

from .models import (
    InvestmentAuthorizationEffect,
    MemberExitEffect,
    PayoutDeferralEffect,
    PenaltyWaiverEffect,
    ProposalEffect,
    ProposalEvaluation,
    ProposalStatus,
    ProposalTally,
    RotationExceptionEffect,
    RotationOrderEffect,
    RotationProposal,
    Ruleset,
    RulesetActivationEffect,
    VoteChoice,
)
from .snapshot_validation import validate_audit_trail, validate_effect_provenance

if TYPE_CHECKING:
    from .registry import GovernanceRegistry


def _freeze_audit_value(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze_audit_value(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_audit_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_audit_value(item) for item in value)
    return value


def _freeze_audit_details(details: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(
        {key: _freeze_audit_value(value) for key, value in details.items()}
    )


@dataclass(frozen=True)
class GovernanceProposalSnapshot:
    """Immutable copy of a proposal and its current lifecycle state."""

    proposal_id: str
    title: str
    description: str
    proposer_id: str
    rotation_order: tuple[str, ...]
    approval_threshold: Decimal
    effective_cycle: int
    created_at: datetime
    voting_deadline: datetime
    status: ProposalStatus
    votes: tuple[tuple[str, VoteChoice], ...]
    eligible_member_ids: tuple[str, ...]
    current_cycle: int
    quorum_numerator: int
    quorum_denominator: int
    opened_at: datetime | None
    evaluation: ProposalEvaluation | None
    effect: ProposalEffect

    def __post_init__(self) -> None:
        object.__setattr__(self, "rotation_order", tuple(self.rotation_order))
        object.__setattr__(
            self,
            "votes",
            tuple(
                sorted(
                    (member_id, VoteChoice(choice)) for member_id, choice in self.votes
                )
            ),
        )
        object.__setattr__(self, "eligible_member_ids", tuple(self.eligible_member_ids))
        object.__setattr__(self, "status", ProposalStatus(self.status))
        if not isinstance(
            self.effect,
            (
                RotationOrderEffect,
                RotationExceptionEffect,
                RulesetActivationEffect,
                InvestmentAuthorizationEffect,
                MemberExitEffect,
                PenaltyWaiverEffect,
                PayoutDeferralEffect,
            ),
        ):
            raise TypeError("Governance proposal snapshots require a typed effect.")

    @classmethod
    def capture(cls, proposal: RotationProposal) -> GovernanceProposalSnapshot:
        """Copy a mutable proposal into an immutable persistence value."""
        if proposal.current_cycle is None:
            raise ValueError("Governance proposal snapshot requires current cycle.")
        if proposal.effect is None:
            raise ValueError("Governance proposal snapshot requires a typed effect.")
        return cls(
            proposal_id=proposal.proposal_id,
            title=proposal.title,
            description=proposal.description,
            proposer_id=proposal.proposer_id,
            rotation_order=proposal.rotation_order,
            approval_threshold=proposal.approval_threshold,
            effective_cycle=proposal.effective_cycle,
            created_at=proposal.created_at,
            voting_deadline=proposal.voting_deadline,
            status=proposal.status,
            votes=tuple(proposal.votes.items()),
            eligible_member_ids=proposal.eligible_member_ids,
            current_cycle=proposal.current_cycle,
            quorum_numerator=proposal.quorum_numerator,
            quorum_denominator=proposal.quorum_denominator,
            opened_at=proposal.opened_at,
            evaluation=proposal.evaluation,
            effect=proposal.effect,
        )

    def restore(self) -> RotationProposal:
        """Reconstruct a mutable proposal from its immutable snapshot value."""
        return RotationProposal(
            proposal_id=self.proposal_id,
            title=self.title,
            description=self.description,
            proposer_id=self.proposer_id,
            rotation_order=self.rotation_order,
            approval_threshold=self.approval_threshold,
            effective_cycle=self.effective_cycle,
            created_at=self.created_at,
            voting_deadline=self.voting_deadline,
            status=self.status,
            votes=dict(self.votes),
            eligible_member_ids=self.eligible_member_ids,
            current_cycle=self.current_cycle,
            quorum_numerator=self.quorum_numerator,
            quorum_denominator=self.quorum_denominator,
            opened_at=self.opened_at,
            evaluation=self.evaluation,
            effect=self.effect,
        )


@dataclass(frozen=True)
class GovernanceSnapshot:
    """Schema-versioned immutable state required to restore governance.

    Audit events retain append order; ``governance_event_ids`` identifies the
    events emitted by this registry when the audit registry is shared.
    """

    schema_version: int
    active_member_ids: tuple[str, ...]
    rotation_versions: tuple[ClassicRotationVersion, ...]
    rotation_exceptions: tuple[ApprovedRotationException, ...]
    proposals: tuple[GovernanceProposalSnapshot, ...]
    rulesets: tuple[Ruleset, ...]
    audit_events: tuple[AuditEvent, ...]
    governance_event_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version < 1:
            raise ValueError("Governance snapshot schema version must be positive.")
        active_members = tuple(sorted(self.active_member_ids))
        if not active_members or any(not item.strip() for item in active_members):
            raise ValueError("Governance snapshot requires non-empty active members.")
        if len(set(active_members)) != len(active_members):
            raise ValueError("Governance snapshot active members must be unique.")
        if any(
            not isinstance(item, ClassicRotationVersion)
            for item in self.rotation_versions
        ):
            raise TypeError("Governance snapshots require rotation version values.")
        if any(
            not isinstance(item, ApprovedRotationException)
            for item in self.rotation_exceptions
        ):
            raise TypeError("Governance snapshots require rotation exception values.")
        if any(
            not isinstance(item, GovernanceProposalSnapshot) for item in self.proposals
        ):
            raise TypeError("Governance snapshots require proposal snapshot values.")
        if any(not isinstance(item, Ruleset) for item in self.rulesets):
            raise TypeError("Governance snapshots require ruleset values.")
        if any(not isinstance(item, AuditEvent) for item in self.audit_events):
            raise TypeError("Governance snapshots require audit event values.")
        object.__setattr__(self, "active_member_ids", active_members)
        object.__setattr__(
            self,
            "rotation_versions",
            tuple(
                sorted(
                    self.rotation_versions,
                    key=lambda item: (item.effective_cycle, item.version),
                )
            ),
        )
        object.__setattr__(
            self,
            "rotation_exceptions",
            tuple(sorted(self.rotation_exceptions, key=lambda item: item.cycle_number)),
        )
        object.__setattr__(self, "proposals", tuple(self.proposals))
        object.__setattr__(
            self,
            "rulesets",
            tuple(
                sorted(
                    self.rulesets,
                    key=lambda item: (item.effective_cycle, item.version),
                )
            ),
        )
        object.__setattr__(
            self,
            "audit_events",
            tuple(
                AuditEvent(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    aggregate_type=event.aggregate_type,
                    aggregate_id=event.aggregate_id,
                    occurred_at=event.occurred_at,
                    actor_id=event.actor_id,
                    source_event=event.source_event,
                    details=_freeze_audit_details(event.details),
                )
                for event in self.audit_events
            ),
        )
        event_ids = tuple(self.governance_event_ids)
        if len(set(event_ids)) != len(event_ids):
            raise ValueError("Governance snapshot event identifiers must be unique.")
        if not set(event_ids).issubset({item.event_id for item in self.audit_events}):
            raise ValueError("Governance snapshot references an unknown audit event.")
        event_id_set = set(event_ids)
        object.__setattr__(
            self,
            "governance_event_ids",
            tuple(
                item.event_id
                for item in self.audit_events
                if item.event_id in event_id_set
            ),
        )

    def to_registry(
        self,
        registry_type: type[GovernanceRegistry] | None = None,
    ) -> GovernanceRegistry:
        """Restore a fresh registry, rejecting unsupported or inconsistent state.

        Args:
            registry_type: Registry class to instantiate; defaults to
                ``GovernanceRegistry``.

        Returns:
            A registry restored from this snapshot.

        Raises:
            ValueError: If the schema or snapshot state is inconsistent.
        """
        from .registry import GovernanceRegistry

        registry_class = registry_type or GovernanceRegistry
        if self.schema_version != 1:
            raise ValueError(
                f"Unsupported governance snapshot schema {self.schema_version}."
            )
        if not self.rotation_versions:
            raise ValueError("Governance snapshot requires rotation versions.")
        schedule = ClassicRotationSchedule(
            self.rotation_versions,
            self.rotation_exceptions,
        )
        if schedule.version_for_cycle(1).effective_cycle != 1:
            raise ValueError(
                "Governance snapshot requires an initial cycle-1 rotation."
            )
        if not any(
            item.version == 1
            and item.effective_cycle == 1
            and item.source_event == "initial-governance-rotation"
            for item in schedule.versions
        ):
            raise ValueError("Governance snapshot is missing its initial rotation.")
        if len({item.version for item in schedule.versions}) != len(schedule.versions):
            raise ValueError("Snapshot rotation version numbers must be unique.")
        if len({item.version for item in self.rulesets}) != len(self.rulesets):
            raise ValueError("Snapshot ruleset versions must be unique.")

        audit_registry = AuditEventRegistry()
        events_by_id: dict[str, AuditEvent] = {}
        for event in self.audit_events:
            copied = audit_registry.record(
                event_id=event.event_id,
                event_type=event.event_type,
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                occurred_at=event.occurred_at,
                actor_id=event.actor_id,
                source_event=event.source_event,
                details=event.details,
            )
            events_by_id[copied.event_id] = copied

        proposals: dict[str, RotationProposal] = {}
        for saved_proposal in self.proposals:
            if saved_proposal.proposal_id in proposals:
                raise ValueError(
                    f"Duplicate proposal {saved_proposal.proposal_id!r} in snapshot."
                )
            proposal = saved_proposal.restore()
            _validate_proposal_state(proposal)
            proposals[proposal.proposal_id] = proposal

        validate_effect_provenance(
            schedule,
            tuple(proposals.values()),
            self.rulesets,
            events_by_id,
            set(self.governance_event_ids),
        )
        validate_audit_trail(
            tuple(proposals.values()),
            self.active_member_ids,
            self.rulesets,
            tuple(events_by_id[event_id] for event_id in self.governance_event_ids),
        )
        registry = registry_class.__new__(registry_class)
        registry._active_members = frozenset(self.active_member_ids)
        registry._rotation_schedule = schedule
        registry._proposals = proposals
        registry._rulesets = list(self.rulesets)
        registry._audit_registry = audit_registry
        registry._audit_event_ids = set(self.governance_event_ids)
        return registry


def _validate_proposal_state(proposal: RotationProposal) -> None:
    if not proposal.eligible_member_ids or proposal.current_cycle is None:
        raise ValueError("Snapshot proposal must retain electorate and cycle context.")
    if proposal.proposer_id not in proposal.eligible_member_ids:
        raise ValueError("Snapshot proposal proposer must belong to its electorate.")
    if proposal.status is ProposalStatus.DRAFT:
        if proposal.opened_at is not None or proposal.votes or proposal.evaluation:
            raise ValueError("Draft snapshot proposal contains voting state.")
    elif proposal.status is ProposalStatus.OPEN:
        if proposal.opened_at is None or proposal.evaluation is not None:
            raise ValueError("Open snapshot proposal has inconsistent lifecycle state.")
    elif proposal.status in {ProposalStatus.APPROVED, ProposalStatus.REJECTED}:
        if proposal.opened_at is None or proposal.evaluation is None:
            raise ValueError("Evaluated snapshot proposal is missing its evaluation.")
        if proposal.evaluation.status is not proposal.status:
            raise ValueError("Snapshot proposal status does not match evaluation.")
        expected_tally = _tally_snapshot_proposal(proposal)
        if proposal.evaluation.tally != expected_tally:
            raise ValueError("Snapshot proposal evaluation tally is inconsistent.")
        if expected_tally.approved != (proposal.status is ProposalStatus.APPROVED):
            raise ValueError("Snapshot proposal result does not match its votes.")
    else:
        raise ValueError(f"Unsupported snapshot proposal status {proposal.status!r}.")


def _tally_snapshot_proposal(proposal: RotationProposal) -> ProposalTally:
    eligible_count = len(proposal.eligible_member_ids)
    yes_count = sum(choice is VoteChoice.YES for choice in proposal.votes.values())
    no_count = sum(choice is VoteChoice.NO for choice in proposal.votes.values())
    abstain_count = sum(
        choice is VoteChoice.ABSTAIN for choice in proposal.votes.values()
    )
    participation_count = yes_count + no_count + abstain_count
    quorum_required = (
        proposal.quorum_numerator * eligible_count + proposal.quorum_denominator - 1
    ) // proposal.quorum_denominator
    quorum_met = participation_count >= quorum_required
    yes_percentage = Decimal(yes_count * 100) / Decimal(eligible_count)
    threshold_met = yes_percentage >= proposal.approval_threshold
    return ProposalTally(
        eligible_count=eligible_count,
        yes_count=yes_count,
        no_count=no_count,
        abstain_count=abstain_count,
        non_voting_count=eligible_count - participation_count,
        quorum_required=quorum_required,
        quorum_met=quorum_met,
        yes_percentage=yes_percentage,
        approval_threshold=proposal.approval_threshold,
        threshold_met=threshold_met,
        approved=quorum_met and threshold_met,
    )
