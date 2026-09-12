"""Repository protocol declarations for future persistence adapters."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from tontine.audit import AuditEvent
from tontine.classic import ClassicPayout, ClassicRotation
from tontine.contributions import ContributionCycle
from tontine.governance import RotationProposal, Ruleset
from tontine.investments import InvestmentActivity
from tontine.ledger import JournalEntry
from tontine.members import Member


@runtime_checkable
class CycleRepository(Protocol):
    """Storage boundary for contribution cycles."""

    def add(self, cycle: ContributionCycle) -> None:
        """Add a cycle or raise for a duplicate cycle identifier."""

    def get(self, cycle_id: str) -> ContributionCycle:
        """Return a cycle or raise KeyError when missing."""

    def list(self) -> Sequence[ContributionCycle]:
        """Return cycles in deterministic identifier order."""


@runtime_checkable
class LedgerRepository(Protocol):
    """Persistence boundary for posted ledger journals."""

    def post(self, journal: JournalEntry) -> None:
        """Post a journal through the ledger's balancing rules."""

    def balance_for(self, account_id: str, currency: str) -> object:
        """Return a derived account balance."""


@runtime_checkable
class InvestmentRepository(Protocol):
    """Storage boundary for investment activity records."""

    def add_activity(self, activity: InvestmentActivity) -> None:
        """Store immutable activity by event identifier."""

    def activities(self) -> Sequence[InvestmentActivity]:
        """Return activities in deterministic event order."""



@runtime_checkable
class MemberRepository(Protocol):
    """Storage boundary for member identity and lifecycle records."""

    def add(self, member: Member) -> None:
        """Add a member or raise for a duplicate member identifier."""

    def get(self, member_id: str) -> Member:
        """Return a member or raise KeyError when missing."""

    def list(self) -> Sequence[Member]:
        """Return members in deterministic identifier order."""


@runtime_checkable
class ClassicRepository(Protocol):
    """Storage boundary for Classic rotations and payout decisions."""

    def save_rotation(self, rotation_id: str, rotation: ClassicRotation) -> None:
        """Save a rotation version or raise for a duplicate identifier."""

    def get_rotation(self, rotation_id: str) -> ClassicRotation:
        """Return a rotation or raise KeyError when missing."""

    def record_payout(self, payout: ClassicPayout) -> None:
        """Record a payout or raise for a duplicate cycle."""

    def payouts(self) -> Sequence[ClassicPayout]:
        """Return historical payouts in deterministic cycle order."""


@runtime_checkable
class GovernanceRepository(Protocol):
    """Storage boundary for proposals, votes, and ruleset versions."""

    def save_proposal(self, proposal: RotationProposal) -> None:
        """Save a proposal or raise for a duplicate proposal identifier."""

    def get_proposal(self, proposal_id: str) -> RotationProposal:
        """Return a proposal or raise KeyError when missing."""

    def save_ruleset(self, ruleset: Ruleset) -> None:
        """Save a ruleset version or raise for a duplicate version."""


@runtime_checkable
class AuditRepository(Protocol):
    """Storage boundary for the canonical append-only audit stream."""

    def record(self, event: AuditEvent) -> None:
        """Append an audit event or raise for a duplicate event identifier."""

    def all_events(self) -> Sequence[AuditEvent]:
        """Return audit events in deterministic append order."""

    def events_for(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> Sequence[AuditEvent]:
        """Return audit history for one aggregate."""
