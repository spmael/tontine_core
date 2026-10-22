"""Governance proposal, vote, ruleset, and audit registries."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal

from tontine._datetime import require_aware_datetime
from tontine.audit import AuditEvent, AuditEventRegistry
from tontine.classic import (
    ApprovedRotationException,
    ClassicRotation,
    ClassicRotationResolution,
    ClassicRotationSchedule,
    ClassicRotationVersion,
)
from tontine.exceptions import MissingRecordError

from ._investment_authorization import _InvestmentAuthorizations
from ._lifecycle import _ProposalLifecycle
from ._member_decisions import _MemberDecisions
from .models import (
    InvestmentAuthorizationEffect,
    MemberExitEffect,
    PayoutDeferralEffect,
    PenaltyWaiverEffect,
    ProposalEffect,
    ProposalStatus,
    RotationExceptionEffect,
    RotationOrderEffect,
    RotationProposal,
    Ruleset,
    RulesetActivationEffect,
)
from .snapshots import GovernanceProposalSnapshot, GovernanceSnapshot


class GovernanceRegistry(
    _ProposalLifecycle,
    _InvestmentAuthorizations,
    _MemberDecisions,
):
    """Manage governance proposals, votes, effective rotations, and audit events."""

    def __init__(
        self,
        active_member_ids: tuple[str, ...],
        initial_rotation: ClassicRotation,
        audit_registry: AuditEventRegistry | None = None,
    ) -> None:
        active_members = tuple(active_member_ids)
        if not active_members:
            raise ValueError("Governance requires active members.")
        if any(not member_id.strip() for member_id in active_members):
            raise ValueError("Governance member identifiers must be non-empty.")
        if len(set(active_members)) != len(active_members):
            raise ValueError("Governance active members must be unique.")
        if set(initial_rotation.member_ids) != set(active_members):
            raise ValueError("Initial rotation must contain all active members.")
        self._active_members = frozenset(active_members)
        self._rotation_schedule = ClassicRotationSchedule(
            (
                ClassicRotationVersion(
                    version=1,
                    effective_cycle=1,
                    rotation=initial_rotation,
                    source_event="initial-governance-rotation",
                ),
            )
        )
        self._proposals: dict[str, RotationProposal] = {}
        self._rulesets: list[Ruleset] = []
        self._audit_registry = audit_registry or AuditEventRegistry()
        self._audit_event_ids: set[str] = set()

    def create_rotation_proposal(
        self,
        proposal_id: str,
        title: str,
        description: str,
        proposer_id: str,
        rotation_order: tuple[str, ...],
        approval_threshold: Decimal,
        effective_cycle: int,
        current_cycle: int,
        created_at: datetime,
        voting_deadline: datetime,
        *,
        quorum_numerator: int = 2,
        quorum_denominator: int = 3,
    ) -> RotationProposal:
        """Create a draft rotation proposal with a frozen electorate.

        Args:
            proposal_id: Unique proposal identifier.
            title: Short proposal title.
            description: Decision context presented to voters.
            proposer_id: Eligible member creating the proposal.
            rotation_order: Candidate order containing every active member once.
            approval_threshold: Required yes-vote percentage of the electorate.
            effective_cycle: First cycle using the approved order.
            current_cycle: Explicit current cycle; effective cycle must be later.
            created_at: Timezone-aware proposal creation timestamp.
            voting_deadline: Timezone-aware last instant at which a vote is valid.
            quorum_numerator: Numerator of the required electorate participation.
            quorum_denominator: Denominator of the required participation fraction.

        Returns:
            A draft proposal with its electorate captured.

        Raises:
            ValueError: If identity, cycle, quorum, threshold, or rotation order
                is invalid.
        """
        if proposal_id in self._proposals:
            raise ValueError(f"Proposal {proposal_id!r} already exists.")
        if proposer_id not in self._active_members:
            raise ValueError("Proposal proposer must be an eligible member.")
        require_aware_datetime(created_at, "created_at")
        require_aware_datetime(voting_deadline, "voting_deadline")
        if current_cycle < 1 or effective_cycle <= current_cycle:
            raise ValueError(
                "Proposal effective cycle must be greater than current cycle."
            )
        rotation = ClassicRotation.from_active_members(rotation_order)
        if set(rotation.member_ids) != self._active_members:
            raise ValueError("Proposed rotation must contain all active members.")
        return self._create_proposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            proposer_id=proposer_id,
            rotation_order=rotation.member_ids,
            effect=RotationOrderEffect(rotation, effective_cycle),
            approval_threshold=approval_threshold,
            effective_cycle=effective_cycle,
            current_cycle=current_cycle,
            created_at=created_at,
            voting_deadline=voting_deadline,
            quorum_numerator=quorum_numerator,
            quorum_denominator=quorum_denominator,
        )

    def create_rotation_exception_proposal(
        self,
        proposal_id: str,
        title: str,
        description: str,
        proposer_id: str,
        exception_id: str,
        recipient_id: str,
        cycle_number: int,
        current_cycle: int,
        approval_threshold: Decimal,
        created_at: datetime,
        voting_deadline: datetime,
        *,
        quorum_numerator: int = 2,
        quorum_denominator: int = 3,
    ) -> RotationProposal:
        """Create a proposal to override one cycle's recipient without a new order.

        Args:
            proposal_id: Unique proposal identifier.
            title: Short proposal title.
            description: Decision context presented to voters.
            proposer_id: Eligible member creating the proposal.
            exception_id: Unique identifier for the approved exception.
            recipient_id: Member proposed as the cycle's recipient.
            cycle_number: One-based cycle affected by the override.
            current_cycle: Explicit current cycle; target cycle must be later.
            approval_threshold: Required yes-vote percentage of the electorate.
            created_at: Timezone-aware proposal creation timestamp.
            voting_deadline: Timezone-aware last instant at which a vote is valid.
            quorum_numerator: Numerator of the required electorate participation.
            quorum_denominator: Denominator of the required participation fraction.

        Returns:
            A draft proposal with a frozen electorate and typed exception effect.

        Raises:
            ValueError: If the cycle conflicts with an existing exception,
                recipient, proposer, threshold, or timing is invalid.
            MissingRecordError: If no base rotation applies to the cycle.
        """
        if any(
            item.cycle_number == cycle_number
            for item in self._rotation_schedule.exceptions
        ):
            raise ValueError(f"Cycle {cycle_number} already has a rotation exception.")
        if any(
            isinstance(item.effect, RotationExceptionEffect)
            and (
                item.effect.cycle_number == cycle_number
                or item.effect.exception_id == exception_id
            )
            and item.status in {ProposalStatus.DRAFT, ProposalStatus.OPEN}
            for item in self._proposals.values()
        ):
            raise ValueError(
                f"Cycle {cycle_number} or exception {exception_id!r} already has "
                "a pending exception."
            )
        if any(
            item.exception_id == exception_id
            for item in self._rotation_schedule.exceptions
        ):
            raise ValueError(f"Rotation exception {exception_id!r} already exists.")
        base_rotation = self._rotation_schedule.version_for_cycle(cycle_number).rotation
        if recipient_id not in base_rotation.member_ids:
            raise ValueError(
                "Rotation exception recipient must belong to the effective rotation."
            )
        return self._create_proposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            proposer_id=proposer_id,
            rotation_order=(),
            effect=RotationExceptionEffect(
                exception_id=exception_id,
                recipient_id=recipient_id,
                cycle_number=cycle_number,
            ),
            approval_threshold=approval_threshold,
            effective_cycle=cycle_number,
            current_cycle=current_cycle,
            created_at=created_at,
            voting_deadline=voting_deadline,
            quorum_numerator=quorum_numerator,
            quorum_denominator=quorum_denominator,
        )

    def create_ruleset_proposal(
        self,
        proposal_id: str,
        title: str,
        description: str,
        proposer_id: str,
        ruleset: Ruleset,
        current_cycle: int,
        approval_threshold: Decimal,
        created_at: datetime,
        voting_deadline: datetime,
        *,
        quorum_numerator: int = 2,
        quorum_denominator: int = 3,
    ) -> RotationProposal:
        """Create a proposal to activate a typed immutable ruleset.

        Args:
            proposal_id: Unique proposal identifier.
            title: Short proposal title.
            description: Decision context presented to voters.
            proposer_id: Eligible member creating the proposal.
            ruleset: Immutable rule version to activate on approval.
            current_cycle: Explicit current cycle; ruleset cycle must be later.
            approval_threshold: Required yes-vote percentage of the electorate.
            created_at: Timezone-aware proposal creation timestamp.
            voting_deadline: Timezone-aware last instant at which a vote is valid.
            quorum_numerator: Numerator of the required electorate participation.
            quorum_denominator: Denominator of the required participation fraction.

        Returns:
            A draft proposal with a frozen electorate and typed ruleset effect.

        Raises:
            ValueError: If the proposal context or ruleset version is invalid.
        """
        self._ensure_ruleset_version_available(ruleset.version)
        return self._create_proposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            proposer_id=proposer_id,
            rotation_order=(),
            effect=RulesetActivationEffect(ruleset),
            approval_threshold=approval_threshold,
            effective_cycle=ruleset.effective_cycle,
            current_cycle=current_cycle,
            created_at=created_at,
            voting_deadline=voting_deadline,
            quorum_numerator=quorum_numerator,
            quorum_denominator=quorum_denominator,
        )

    def _create_proposal(
        self,
        *,
        proposal_id: str,
        title: str,
        description: str,
        proposer_id: str,
        rotation_order: tuple[str, ...],
        effect: ProposalEffect,
        approval_threshold: Decimal,
        effective_cycle: int,
        current_cycle: int,
        created_at: datetime,
        voting_deadline: datetime,
        quorum_numerator: int,
        quorum_denominator: int,
        eligible_member_ids: tuple[str, ...] | None = None,
    ) -> RotationProposal:
        if proposal_id in self._proposals:
            raise ValueError(f"Proposal {proposal_id!r} already exists.")
        if proposer_id not in self._active_members:
            raise ValueError("Proposal proposer must be an eligible member.")
        electorate = tuple(
            self._active_members if eligible_member_ids is None else eligible_member_ids
        )
        if not electorate:
            raise ValueError("Proposal electorate cannot be empty after recusal.")
        if proposer_id not in electorate:
            raise ValueError(
                "Proposal proposer must belong to its eligible electorate."
            )
        require_aware_datetime(created_at, "created_at")
        require_aware_datetime(voting_deadline, "voting_deadline")
        immediate_effect = isinstance(
            effect, (MemberExitEffect, PenaltyWaiverEffect, PayoutDeferralEffect)
        )
        if current_cycle < 1 or (
            effective_cycle < current_cycle
            if immediate_effect
            else effective_cycle <= current_cycle
        ):
            raise ValueError(
                "Proposal effect cycle must be current or strictly future as required."
            )
        proposal = RotationProposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            proposer_id=proposer_id,
            rotation_order=rotation_order,
            approval_threshold=approval_threshold,
            effective_cycle=effective_cycle,
            created_at=created_at,
            voting_deadline=voting_deadline,
            eligible_member_ids=electorate,
            current_cycle=current_cycle,
            quorum_numerator=quorum_numerator,
            quorum_denominator=quorum_denominator,
            effect=effect,
        )
        self._proposals[proposal_id] = proposal
        self._audit("proposal_created", proposal_id, created_at)
        return proposal

    def rotation_for_cycle(self, cycle_number: int) -> ClassicRotation:
        """Return the base rotation order effective for a cycle."""
        return self._rotation_schedule.version_for_cycle(cycle_number).rotation

    def resolve_rotation_for_cycle(
        self,
        cycle_number: int,
    ) -> ClassicRotationResolution:
        """Return the base rotation and any approved cycle recipient override."""
        return self._rotation_schedule.resolve_cycle(cycle_number)

    def audit_events(
        self,
        aggregate_id: str,
        *,
        aggregate_type: str = "proposal",
    ) -> tuple[AuditEvent, ...]:
        """Return immutable audit events for one governance aggregate."""
        return self._audit_registry.events_for(aggregate_type, aggregate_id)

    def snapshot(self) -> GovernanceSnapshot:
        """Capture complete governance state in immutable schema version 1.

        Returns:
            A detached snapshot of registry state and append-ordered audit history.
        """
        audit_events = self._audit_registry.all_events()
        return GovernanceSnapshot(
            schema_version=1,
            active_member_ids=tuple(self._active_members),
            rotation_versions=self._rotation_schedule.versions,
            rotation_exceptions=self._rotation_schedule.exceptions,
            proposals=tuple(
                GovernanceProposalSnapshot.capture(proposal)
                for proposal in self._proposals.values()
            ),
            rulesets=tuple(self._rulesets),
            audit_events=audit_events,
            governance_event_ids=tuple(
                event.event_id
                for event in audit_events
                if event.event_id in self._audit_event_ids
            ),
        )

    @classmethod
    def from_snapshot(cls, snapshot: GovernanceSnapshot) -> GovernanceRegistry:
        """Restore a registry from a supported, internally consistent snapshot.

        Args:
            snapshot: Versioned snapshot produced by a governance registry.

        Returns:
            A registry with equivalent state and audit history.

        Raises:
            TypeError: If ``snapshot`` is not a governance snapshot.
            ValueError: If its schema is unsupported or state is inconsistent.
        """
        if not isinstance(snapshot, GovernanceSnapshot):
            raise TypeError("Expected a GovernanceSnapshot.")
        return snapshot.to_registry(cls)

    def add_ruleset(
        self,
        ruleset: Ruleset,
        *,
        occurred_at: datetime,
    ) -> None:
        """Add an immutable ruleset using an explicit occurrence time."""
        require_aware_datetime(occurred_at, "occurred_at")
        self._ensure_ruleset_version_available(ruleset.version)
        self._rulesets.append(ruleset)
        self._rulesets.sort(key=lambda item: (item.effective_cycle, item.version))
        self._audit(
            "ruleset_added",
            ruleset.ruleset_id,
            occurred_at,
            details={"version": ruleset.version},
        )

    def _ensure_ruleset_version_available(
        self,
        version: int,
        *,
        excluding_proposal_id: str | None = None,
    ) -> None:
        if any(existing.version == version for existing in self._rulesets):
            raise ValueError(f"Ruleset version {version} already exists.")
        if any(
            isinstance(proposal.effect, RulesetActivationEffect)
            and proposal.effect.ruleset.version == version
            and proposal.status in {ProposalStatus.DRAFT, ProposalStatus.OPEN}
            and proposal.proposal_id != excluding_proposal_id
            for proposal in self._proposals.values()
        ):
            raise ValueError(
                f"Ruleset version {version} already has a pending proposal."
            )

    def _prevalidate_effect(self, proposal: RotationProposal) -> None:
        effect = proposal.effect
        if isinstance(effect, RotationExceptionEffect):
            if any(
                item.cycle_number == effect.cycle_number
                for item in self._rotation_schedule.exceptions
            ):
                raise ValueError(
                    f"Cycle {effect.cycle_number} already has a rotation exception."
                )
            base_rotation = self._rotation_schedule.version_for_cycle(
                effect.cycle_number
            ).rotation
            if effect.recipient_id not in base_rotation.member_ids:
                raise ValueError(
                    "Rotation exception recipient is not in the approved base order."
                )
        elif isinstance(effect, RulesetActivationEffect):
            self._ensure_ruleset_version_available(
                effect.ruleset.version,
                excluding_proposal_id=proposal.proposal_id,
            )
        elif isinstance(
            effect, (MemberExitEffect, PenaltyWaiverEffect, PayoutDeferralEffect)
        ):
            self._prevalidate_member_decision(proposal)

    def _activate_effect(
        self,
        proposal: RotationProposal,
        occurred_at: datetime,
    ) -> None:
        effect = proposal.effect
        if isinstance(effect, RotationOrderEffect):
            version_number = (
                max(item.version for item in self._rotation_schedule.versions) + 1
            )
            approval_event = self._audit(
                "rotation_approved", proposal.proposal_id, occurred_at
            )
            self._rotation_schedule = self._rotation_schedule.with_version(
                ClassicRotationVersion(
                    version=version_number,
                    effective_cycle=effect.effective_cycle,
                    rotation=effect.rotation,
                    source_event=approval_event.event_id,
                )
            )
        elif isinstance(effect, RotationExceptionEffect):
            approval_event = self._audit(
                "rotation_exception_approved",
                proposal.proposal_id,
                occurred_at,
                details={
                    "cycle_number": effect.cycle_number,
                    "recipient_id": effect.recipient_id,
                },
            )
            self._rotation_schedule = self._rotation_schedule.with_exception(
                ApprovedRotationException(
                    exception_id=effect.exception_id,
                    cycle_number=effect.cycle_number,
                    recipient_id=effect.recipient_id,
                    proposal_id=proposal.proposal_id,
                    approval_event_id=approval_event.event_id,
                    approved_at=occurred_at,
                )
            )
        elif isinstance(effect, RulesetActivationEffect):
            self._audit(
                "ruleset_activated",
                proposal.proposal_id,
                occurred_at,
                details={
                    "ruleset_id": effect.ruleset.ruleset_id,
                    "proposal_id": proposal.proposal_id,
                    "version": effect.ruleset.version,
                },
            )
            self._rulesets.append(effect.ruleset)
            self._rulesets.sort(key=lambda item: (item.effective_cycle, item.version))
        elif isinstance(effect, InvestmentAuthorizationEffect):
            self._audit(
                "investment_authorization_approved",
                proposal.proposal_id,
                occurred_at,
                details={
                    "asset_id": effect.asset_id,
                    "activity_type": effect.activity_type.value,
                    "max_amount": str(effect.max_amount),
                    "currency": str(effect.currency),
                },
            )
        elif isinstance(
            effect, (MemberExitEffect, PenaltyWaiverEffect, PayoutDeferralEffect)
        ):
            self._activate_member_decision(proposal, occurred_at)
        else:
            raise TypeError(
                "Proposal effect must be a supported typed decision effect."
            )

    def ruleset_for_cycle(self, cycle_number: int) -> Ruleset:
        """Return the latest ruleset effective for a cycle.

        Raises:
            ValueError: If ``cycle_number`` is not positive.
            MissingRecordError: If no ruleset applies to the cycle.
        """
        if cycle_number < 1:
            raise ValueError("Ruleset cycle number must be positive.")
        applicable = [
            item for item in self._rulesets if item.effective_cycle <= cycle_number
        ]
        if not applicable:
            raise MissingRecordError(
                f"No ruleset is effective for cycle {cycle_number}."
            )
        return max(applicable, key=lambda item: (item.effective_cycle, item.version))

    def _audit(
        self,
        event_type: str,
        aggregate_id: str,
        occurred_at: datetime,
        *,
        aggregate_type: str = "proposal",
        details: Mapping[str, object] | None = None,
    ) -> AuditEvent:
        event_number = len(self._audit_registry.all_events()) + 1
        event = self._audit_registry.record(
            event_id=f"{event_type}:{aggregate_id}:{event_number}",
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            occurred_at=occurred_at,
            actor_id=None,
            source_event=None,
            details=details or {"source": "governance"},
        )
        self._audit_event_ids.add(event.event_id)
        return event


__all__ = ["GovernanceRegistry"]
