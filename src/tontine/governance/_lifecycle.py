"""Proposal lifecycle operations shared by the public governance registry."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal

from tontine._datetime import require_aware_datetime
from tontine.audit import AuditEvent, AuditEventRegistry
from tontine.exceptions import MissingRecordError

from .models import (
    ProposalEvaluation,
    ProposalStatus,
    ProposalTally,
    RotationProposal,
    VoteChoice,
)


class _ProposalLifecycle:
    """Implement proposal lifecycle behavior over registry-owned state."""

    _active_members: frozenset[str]
    _proposals: dict[str, RotationProposal]
    _audit_registry: AuditEventRegistry
    _audit_event_ids: set[str]

    def _audit(
        self,
        event_type: str,
        aggregate_id: str,
        occurred_at: datetime,
        *,
        aggregate_type: str = "proposal",
        details: Mapping[str, object] | None = None,
    ) -> AuditEvent:
        raise NotImplementedError

    def _prevalidate_effect(self, proposal: RotationProposal) -> None:
        raise NotImplementedError

    def _activate_effect(
        self,
        proposal: RotationProposal,
        occurred_at: datetime,
    ) -> None:
        raise NotImplementedError

    def set_active_members(
        self,
        active_member_ids: tuple[str, ...],
        *,
        occurred_at: datetime,
    ) -> None:
        """Replace current membership without changing existing electorates.

        Args:
            active_member_ids: Unique, non-empty current member identifiers.
            occurred_at: Timezone-aware membership change time.
        """
        require_aware_datetime(occurred_at, "occurred_at")
        members = tuple(active_member_ids)
        if not members or any(not member_id.strip() for member_id in members):
            raise ValueError("Governance requires non-empty active member IDs.")
        if len(set(members)) != len(members):
            raise ValueError("Governance active members must be unique.")
        if frozenset(members) == self._active_members:
            raise ValueError("Active membership must change.")
        self._active_members = frozenset(members)
        self._audit(
            "active_members_changed",
            "active_members",
            occurred_at,
            aggregate_type="governance",
            details={"member_ids": tuple(sorted(self._active_members))},
        )

    def open_proposal(
        self,
        proposal_id: str,
        *,
        occurred_at: datetime,
    ) -> None:
        """Open a draft proposal for voting at an explicit occurrence time.

        Raises:
            ValueError: If the state transition or timestamp is invalid.
            MissingRecordError: If the proposal does not exist.
        """
        require_aware_datetime(occurred_at, "occurred_at")
        proposal = self._proposal(proposal_id)
        if proposal.status is not ProposalStatus.DRAFT:
            raise ValueError("Only draft proposals can be opened.")
        if not proposal.created_at <= occurred_at <= proposal.voting_deadline:
            raise ValueError("Proposal open time must be within its lifecycle.")
        proposal.status = ProposalStatus.OPEN
        proposal.opened_at = occurred_at
        self._audit("proposal_opened", proposal_id, occurred_at)

    def vote(
        self,
        proposal_id: str,
        member_id: str,
        choice: VoteChoice,
        *,
        occurred_at: datetime,
    ) -> None:
        """Record one electorate member's vote before or at the deadline.

        Args:
            proposal_id: Proposal receiving the vote.
            member_id: Member whose eligibility was frozen on the proposal.
            choice: Yes, no, or abstain.
            occurred_at: Timezone-aware vote occurrence timestamp.

        Raises:
            ValueError: If the proposal is not open, the member is ineligible,
                the vote is duplicated, or the time is outside the voting window.
            MissingRecordError: If the proposal does not exist.
        """
        require_aware_datetime(occurred_at, "occurred_at")
        proposal = self._proposal(proposal_id)
        if proposal.status is not ProposalStatus.OPEN:
            raise ValueError("Only open proposals can receive votes.")
        if proposal.opened_at is None or occurred_at < proposal.opened_at:
            raise ValueError("Vote time cannot precede proposal opening.")
        if occurred_at > proposal.voting_deadline:
            raise ValueError("Vote time cannot be after the proposal deadline.")
        if member_id not in proposal.eligible_member_ids:
            raise ValueError(
                "Voter must be eligible in the proposal's frozen electorate."
            )
        if member_id in proposal.votes:
            raise ValueError(f"Member {member_id!r} has already voted.")
        vote_choice = VoteChoice(choice)
        proposal.votes[member_id] = vote_choice
        self._audit(
            "vote_submitted",
            proposal_id,
            occurred_at,
            details={"member_id": member_id, "choice": vote_choice.value},
        )

    def evaluate(
        self,
        proposal_id: str,
        *,
        occurred_at: datetime,
    ) -> ProposalStatus:
        """Evaluate after full participation or at/after the deadline.

        The approval threshold is yes votes divided by the frozen electorate.
        Abstentions contribute to quorum only. The default quorum is two-thirds
        of eligible members, rounded up to a whole voter.

        Raises:
            ValueError: If evaluation is too early, precedes a vote, or uses a
                naive timestamp.
            MissingRecordError: If the proposal does not exist.
        """
        require_aware_datetime(occurred_at, "occurred_at")
        proposal = self._proposal(proposal_id)
        if proposal.status is not ProposalStatus.OPEN:
            return proposal.status
        all_voted = len(proposal.votes) == len(proposal.eligible_member_ids)
        if occurred_at < proposal.voting_deadline and not all_voted:
            raise ValueError(
                "Proposal can be evaluated early only after every eligible member "
                "has voted."
            )
        latest_vote_at = max(
            (
                event.occurred_at
                for event in self._audit_registry.events_for("proposal", proposal_id)
                if event.event_id in self._audit_event_ids
                and event.event_type == "vote_submitted"
            ),
            default=proposal.opened_at,
        )
        if latest_vote_at is not None and occurred_at < latest_vote_at:
            raise ValueError("Proposal evaluation cannot precede its latest vote.")
        tally = self._tally(proposal)
        status = ProposalStatus.APPROVED if tally.approved else ProposalStatus.REJECTED
        if status is ProposalStatus.APPROVED:
            self._prevalidate_effect(proposal)
        evaluation = ProposalEvaluation(status, occurred_at, tally)
        proposal.status = status
        proposal.evaluation = evaluation
        self._audit(
            "proposal_evaluated",
            proposal_id,
            occurred_at,
            details={
                "status": status.value,
                "eligible": tally.eligible_count,
                "yes": tally.yes_count,
                "no": tally.no_count,
                "abstain": tally.abstain_count,
                "non_voting": tally.non_voting_count,
                "quorum_required": tally.quorum_required,
                "quorum_met": tally.quorum_met,
                "threshold_met": tally.threshold_met,
            },
        )
        if status is ProposalStatus.APPROVED:
            self._activate_effect(proposal, occurred_at)
        return status

    def tally_for_proposal(self, proposal_id: str) -> ProposalTally:
        """Return the current immutable vote tally for one proposal."""
        return self._tally(self._proposal(proposal_id))

    def evaluation_for_proposal(self, proposal_id: str) -> ProposalEvaluation:
        """Return the recorded evaluation or raise if the proposal is unevaluated."""
        proposal = self._proposal(proposal_id)
        if proposal.evaluation is None:
            raise MissingRecordError(
                f"Proposal {proposal_id!r} has not been evaluated."
            )
        return proposal.evaluation

    def _tally(self, proposal: RotationProposal) -> ProposalTally:
        eligible_count = len(proposal.eligible_member_ids)
        if eligible_count < 1:
            raise ValueError("Proposal electorate cannot be empty.")
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

    def _proposal(self, proposal_id: str) -> RotationProposal:
        try:
            return self._proposals[proposal_id]
        except KeyError as exc:
            raise MissingRecordError(
                f"Proposal {proposal_id!r} was not found."
            ) from exc
