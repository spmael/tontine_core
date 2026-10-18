"""Investment authorization proposals and approved-effect lookup."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from .models import (
    InvestmentAuthorizationEffect,
    ProposalEffect,
    ProposalStatus,
    RotationProposal,
)


class _InvestmentAuthorizations:
    """Create and resolve proposals that authorize investment activity."""

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
    ) -> RotationProposal:
        raise NotImplementedError

    def _proposal(self, proposal_id: str) -> RotationProposal:
        raise NotImplementedError

    def create_investment_authorization_proposal(
        self,
        proposal_id: str,
        title: str,
        description: str,
        proposer_id: str,
        authorization: InvestmentAuthorizationEffect,
        effective_cycle: int,
        current_cycle: int,
        approval_threshold: Decimal,
        created_at: datetime,
        voting_deadline: datetime,
        *,
        quorum_numerator: int = 2,
        quorum_denominator: int = 3,
    ) -> RotationProposal:
        """Create a proposal authorizing a purchase or sale of one asset.

        Args:
            proposal_id: Unique proposal identifier.
            title: Short proposal title.
            description: Decision context presented to voters.
            proposer_id: Eligible member creating the proposal.
            authorization: Asset, activity type, and cumulative maximum in the
                asset currency.
            effective_cycle: Cycle from which the decision applies.
            current_cycle: Explicit current cycle; effective cycle must be later.
            approval_threshold: Required yes-vote percentage of the electorate.
            created_at: Timezone-aware proposal creation timestamp.
            voting_deadline: Timezone-aware last instant at which a vote is valid.
            quorum_numerator: Numerator of the required electorate participation.
            quorum_denominator: Denominator of the required participation fraction.

        Returns:
            A draft proposal with a frozen electorate and typed authorization.

        Raises:
            TypeError: If ``authorization`` is not an investment authorization.
            ValueError: If the proposal context is invalid.
        """
        if not isinstance(authorization, InvestmentAuthorizationEffect):
            raise TypeError("Expected an InvestmentAuthorizationEffect.")
        return self._create_proposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            proposer_id=proposer_id,
            rotation_order=(),
            effect=authorization,
            approval_threshold=approval_threshold,
            effective_cycle=effective_cycle,
            current_cycle=current_cycle,
            created_at=created_at,
            voting_deadline=voting_deadline,
            quorum_numerator=quorum_numerator,
            quorum_denominator=quorum_denominator,
        )

    def approved_investment_authorization(
        self, proposal_id: str
    ) -> InvestmentAuthorizationEffect:
        """Return the effect of an approved investment authorization proposal.

        Raises:
            MissingRecordError: If the proposal does not exist.
            ValueError: If the proposal is not approved or does not authorize
                investment activity.
        """
        proposal = self._proposal(proposal_id)
        if proposal.status is not ProposalStatus.APPROVED:
            raise ValueError(f"Proposal {proposal_id!r} is not approved.")
        if not isinstance(proposal.effect, InvestmentAuthorizationEffect):
            raise ValueError(
                f"Proposal {proposal_id!r} does not authorize investment activity."
            )
        return proposal.effect
