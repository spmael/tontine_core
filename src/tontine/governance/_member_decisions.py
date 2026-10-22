"""Create and resolve governance decisions about member exits and penalties."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal

from tontine._datetime import require_aware_datetime
from tontine.audit import AuditEvent

from .models import (
    MemberExitEffect,
    MemberExitType,
    PayoutDeferralEffect,
    PenaltyWaiverEffect,
    ProposalEffect,
    ProposalStatus,
    RotationProposal,
)


class _MemberDecisions:
    """Add typed member decisions to the shared proposal lifecycle."""

    _active_members: frozenset[str]
    _proposals: dict[str, RotationProposal]

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
        raise NotImplementedError

    def _proposal(self, proposal_id: str) -> RotationProposal:
        raise NotImplementedError

    def _audit(
        self,
        event_type: str,
        aggregate_id: str,
        occurred_at: datetime,
        *,
        details: Mapping[str, object] | None = None,
    ) -> AuditEvent:
        raise NotImplementedError

    def create_member_exit_proposal(
        self,
        proposal_id: str,
        title: str,
        description: str,
        proposer_id: str,
        member_id: str,
        exit_type: MemberExitType,
        exit_date: date,
        request_cycle: int,
        approval_threshold: Decimal,
        created_at: datetime,
        voting_deadline: datetime,
        *,
        quorum_numerator: int = 2,
        quorum_denominator: int = 3,
    ) -> RotationProposal:
        """Create a member-exit decision with the electorate captured at request time.

        Args:
            proposal_id: Unique decision identifier.
            title: Short title presented to voters.
            description: Context for the decision.
            proposer_id: Active member submitting the proposal.
            member_id: Active member whose exit is proposed.
            exit_type: Voluntary exit, expulsion, or death.
            exit_date: Calendar date on which the exit takes effect.
            request_cycle: Current cycle in which the exit was requested.
            approval_threshold: Required yes-vote percentage of eligible members.
            created_at: Timezone-aware proposal creation time.
            voting_deadline: Timezone-aware last instant for voting.
            quorum_numerator: Numerator of the participation quorum.
            quorum_denominator: Denominator of the participation quorum.

        Returns:
            A draft proposal; an expulsion excludes its subject from the electorate.

        Raises:
            ValueError: If the member, cycle, electorate, or proposal is invalid.
        """
        effect = MemberExitEffect(member_id, exit_type, exit_date, request_cycle)
        if member_id not in self._active_members:
            raise ValueError("Exiting member must be active.")
        self._ensure_effect_available(effect, excluding_proposal_id=None)
        eligible = tuple(
            member
            for member in self._active_members
            if not (
                effect.exit_type is MemberExitType.EXPULSION
                and member == effect.member_id
            )
        )
        return self._create_proposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            proposer_id=proposer_id,
            rotation_order=(),
            effect=effect,
            approval_threshold=approval_threshold,
            effective_cycle=request_cycle,
            current_cycle=request_cycle,
            created_at=created_at,
            voting_deadline=voting_deadline,
            quorum_numerator=quorum_numerator,
            quorum_denominator=quorum_denominator,
            eligible_member_ids=eligible,
        )

    def create_penalty_waiver_proposal(
        self,
        proposal_id: str,
        title: str,
        description: str,
        proposer_id: str,
        penalty_assessment_id: str,
        member_id: str,
        current_cycle: int,
        approval_threshold: Decimal,
        created_at: datetime,
        voting_deadline: datetime,
        *,
        quorum_numerator: int = 2,
        quorum_denominator: int = 3,
    ) -> RotationProposal:
        """Create a proposal to waive one member's assessed penalty.

        Args:
            proposal_id: Unique decision identifier.
            title: Short title presented to voters.
            description: Context for the waiver.
            proposer_id: Active member submitting the proposal.
            penalty_assessment_id: Identifier of the assessed penalty.
            member_id: Member who owes the assessed penalty.
            current_cycle: Cycle in which the waiver is proposed.
            approval_threshold: Required yes-vote percentage of eligible members.
            created_at: Timezone-aware proposal creation time.
            voting_deadline: Timezone-aware last instant for voting.
            quorum_numerator: Numerator of the participation quorum.
            quorum_denominator: Denominator of the participation quorum.

        Returns:
            A draft proposal that excludes the assessed member from its electorate.

        Raises:
            ValueError: If the assessment has a pending or approved waiver, or
                the proposal context is invalid.
        """
        effect = PenaltyWaiverEffect(penalty_assessment_id, member_id)
        self._ensure_effect_available(effect, excluding_proposal_id=None)
        eligible = tuple(
            member for member in self._active_members if member != effect.member_id
        )
        return self._create_proposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            proposer_id=proposer_id,
            rotation_order=(),
            effect=effect,
            approval_threshold=approval_threshold,
            effective_cycle=current_cycle,
            current_cycle=current_cycle,
            created_at=created_at,
            voting_deadline=voting_deadline,
            quorum_numerator=quorum_numerator,
            quorum_denominator=quorum_denominator,
            eligible_member_ids=eligible,
        )

    def create_payout_deferral_proposal(
        self,
        proposal_id: str,
        title: str,
        description: str,
        proposer_id: str,
        exit_proposal_id: str,
        reason: str,
        extended_date: date,
        current_cycle: int,
        approval_threshold: Decimal,
        created_at: datetime,
        voting_deadline: datetime,
        *,
        quorum_numerator: int = 2,
        quorum_denominator: int = 3,
    ) -> RotationProposal:
        """Create a reasoned payout extension for an approved member exit.

        The extended date must be more than 12 and at most 24 calendar months
        after the exit date.

        Args:
            proposal_id: Unique decision identifier.
            title: Short title presented to voters.
            description: Context for the deferral.
            proposer_id: Active member submitting the proposal.
            exit_proposal_id: Approved exit decision being extended.
            reason: Recorded reason for extending the payout date.
            extended_date: New payout date as a calendar date.
            current_cycle: Cycle in which the deferral is proposed.
            approval_threshold: Required yes-vote percentage of eligible members.
            created_at: Timezone-aware proposal creation time, after exit approval.
            voting_deadline: Timezone-aware last instant for voting.
            quorum_numerator: Numerator of the participation quorum.
            quorum_denominator: Denominator of the participation quorum.

        Returns:
            A draft proposal linked to the approved exit.

        Raises:
            ValueError: If the exit is not approved, the reason or date is
                invalid, or a deferral already exists for the exit.
        """
        effect = PayoutDeferralEffect(exit_proposal_id, reason, extended_date)
        exit_proposal = self._proposal(exit_proposal_id)
        exit_effect = self.approved_member_exit(exit_proposal_id)
        effect.validate_exit_date(exit_effect.exit_date)
        require_aware_datetime(created_at, "created_at")
        if (
            exit_proposal.evaluation is None
            or created_at < exit_proposal.evaluation.evaluated_at
        ):
            raise ValueError("Payout deferral must follow the approved exit decision.")
        self._ensure_effect_available(effect, excluding_proposal_id=None)
        return self._create_proposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            proposer_id=proposer_id,
            rotation_order=(),
            effect=effect,
            approval_threshold=approval_threshold,
            effective_cycle=current_cycle,
            current_cycle=current_cycle,
            created_at=created_at,
            voting_deadline=voting_deadline,
            quorum_numerator=quorum_numerator,
            quorum_denominator=quorum_denominator,
        )

    def approved_member_exit(self, proposal_id: str) -> MemberExitEffect:
        """Return the approved exit effect.

        Raises:
            MissingRecordError: If the proposal does not exist.
            ValueError: If it is not approved or does not concern a member exit.
        """
        proposal = self._approved_proposal(proposal_id)
        if not isinstance(proposal.effect, MemberExitEffect):
            raise ValueError(f"Proposal {proposal_id!r} is not a member exit decision.")
        return proposal.effect

    def approved_penalty_waiver(self, proposal_id: str) -> PenaltyWaiverEffect:
        """Return the approved penalty-waiver effect.

        Raises:
            MissingRecordError: If the proposal does not exist.
            ValueError: If it is not approved or does not concern a penalty waiver.
        """
        proposal = self._approved_proposal(proposal_id)
        if not isinstance(proposal.effect, PenaltyWaiverEffect):
            raise ValueError(f"Proposal {proposal_id!r} is not a penalty waiver.")
        return proposal.effect

    def approved_payout_deferral(self, proposal_id: str) -> PayoutDeferralEffect:
        """Return the approved payout-deferral effect.

        Raises:
            MissingRecordError: If the proposal does not exist.
            ValueError: If it is not approved or does not concern a payout deferral.
        """
        proposal = self._approved_proposal(proposal_id)
        if not isinstance(proposal.effect, PayoutDeferralEffect):
            raise ValueError(f"Proposal {proposal_id!r} is not a payout deferral.")
        return proposal.effect

    def _approved_proposal(self, proposal_id: str) -> RotationProposal:
        proposal = self._proposal(proposal_id)
        if proposal.status is not ProposalStatus.APPROVED:
            raise ValueError(f"Proposal {proposal_id!r} is not approved.")
        if proposal.effect is None:
            raise ValueError(f"Proposal {proposal_id!r} has no decision effect.")
        return proposal

    def _ensure_effect_available(
        self,
        effect: MemberExitEffect | PenaltyWaiverEffect | PayoutDeferralEffect,
        *,
        excluding_proposal_id: str | None,
    ) -> None:
        for proposal in self._proposals.values():
            if proposal.proposal_id == excluding_proposal_id:
                continue
            existing = proposal.effect
            if proposal.status not in {
                ProposalStatus.DRAFT,
                ProposalStatus.OPEN,
                ProposalStatus.APPROVED,
            }:
                continue
            if isinstance(effect, MemberExitEffect) and isinstance(
                existing, MemberExitEffect
            ):
                duplicate = effect.member_id == existing.member_id
            elif isinstance(effect, PenaltyWaiverEffect) and isinstance(
                existing, PenaltyWaiverEffect
            ):
                duplicate = (
                    effect.penalty_assessment_id == existing.penalty_assessment_id
                )
            elif isinstance(effect, PayoutDeferralEffect) and isinstance(
                existing, PayoutDeferralEffect
            ):
                duplicate = effect.exit_proposal_id == existing.exit_proposal_id
            else:
                duplicate = False
            if duplicate:
                raise ValueError("A matching member decision already exists.")

    def _prevalidate_member_decision(self, proposal: RotationProposal) -> None:
        effect = proposal.effect
        if not isinstance(
            effect, (MemberExitEffect, PenaltyWaiverEffect, PayoutDeferralEffect)
        ):
            return
        self._ensure_effect_available(
            effect,
            excluding_proposal_id=proposal.proposal_id,
        )
        if isinstance(effect, PayoutDeferralEffect):
            exit_effect = self.approved_member_exit(effect.exit_proposal_id)
            effect.validate_exit_date(exit_effect.exit_date)

    def _activate_member_decision(
        self,
        proposal: RotationProposal,
        occurred_at: datetime,
    ) -> None:
        effect = proposal.effect
        if isinstance(effect, MemberExitEffect):
            self._audit(
                "member_exit_approved",
                proposal.proposal_id,
                occurred_at,
                details={
                    "member_id": effect.member_id,
                    "exit_type": effect.exit_type.value,
                    "exit_date": effect.exit_date.isoformat(),
                    "request_cycle": effect.request_cycle,
                },
            )
        elif isinstance(effect, PenaltyWaiverEffect):
            self._audit(
                "penalty_waiver_approved",
                proposal.proposal_id,
                occurred_at,
                details={
                    "penalty_assessment_id": effect.penalty_assessment_id,
                    "member_id": effect.member_id,
                },
            )
        elif isinstance(effect, PayoutDeferralEffect):
            self._audit(
                "payout_deferral_approved",
                proposal.proposal_id,
                occurred_at,
                details={
                    "exit_proposal_id": effect.exit_proposal_id,
                    "reason": effect.reason,
                    "extended_date": effect.extended_date.isoformat(),
                },
            )
