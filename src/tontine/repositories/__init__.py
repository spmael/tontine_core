"""Typed repository protocols and deterministic in-memory implementations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from tontine.accounts import FinancialAccount
from tontine.audit import AuditEvent
from tontine.classic import ClassicPayout, ClassicRotation
from tontine.contributions import ContributionCycle
from tontine.governance import RotationProposal, Ruleset
from tontine.groups import Group
from tontine.members import Member
from tontine.repositories.protocols import (
    AuditRepository,
    ClassicRepository,
    CycleRepository,
    GovernanceRepository,
    LedgerRepository,
    MemberRepository,
)


@runtime_checkable
class GroupRepository(Protocol):
    """Storage boundary for group aggregates."""

    def add(self, group: Group) -> None:
        """Add a group or raise for a duplicate identifier."""

    def get(self, group_id: str) -> Group:
        """Return a group or raise KeyError when missing."""

    def list(self) -> Sequence[Group]:
        """Return groups in deterministic identifier order."""


@runtime_checkable
class AccountRepository(Protocol):
    """Storage boundary for financial account records."""

    def add(self, account: FinancialAccount) -> None:
        """Add an account or raise for a duplicate identifier."""

    def get(self, account_id: str) -> FinancialAccount:
        """Return an account or raise KeyError when missing."""

    def list(self) -> Sequence[FinancialAccount]:
        """Return accounts in deterministic identifier order."""


class InMemoryGroupRepository:
    """Deterministic in-memory implementation of the group repository."""

    def __init__(self) -> None:
        self._groups: dict[str, Group] = {}

    def add(self, group: Group) -> None:
        """Add a group and reject duplicate identifiers."""
        if group.group_id in self._groups:
            raise ValueError(f"Group {group.group_id!r} is already stored.")
        self._groups[group.group_id] = group

    def get(self, group_id: str) -> Group:
        """Return a group or raise KeyError when missing."""
        try:
            return self._groups[group_id]
        except KeyError as exc:
            raise KeyError(f"Group {group_id!r} was not found.") from exc

    def list(self) -> tuple[Group, ...]:
        """Return groups sorted by stable identifier."""
        return tuple(self._groups[key] for key in sorted(self._groups))


class InMemoryAccountRepository:
    """Deterministic in-memory implementation of the account repository."""

    def __init__(self) -> None:
        self._accounts: dict[str, FinancialAccount] = {}

    def add(self, account: FinancialAccount) -> None:
        """Add an account and reject duplicate identifiers."""
        if account.account_id in self._accounts:
            raise ValueError(f"Account {account.account_id!r} is already stored.")
        self._accounts[account.account_id] = account

    def get(self, account_id: str) -> FinancialAccount:
        """Return an account or raise KeyError when missing."""
        try:
            return self._accounts[account_id]
        except KeyError as exc:
            raise KeyError(f"Account {account_id!r} was not found.") from exc

    def list(self) -> tuple[FinancialAccount, ...]:
        """Return accounts sorted by stable identifier."""
        return tuple(self._accounts[key] for key in sorted(self._accounts))


class InMemoryCycleRepository:
    """Deterministic in-memory implementation of the cycle repository."""

    def __init__(self) -> None:
        self._cycles: dict[str, ContributionCycle] = {}

    def add(self, cycle: ContributionCycle) -> None:
        """Add a cycle and reject duplicate identifiers."""
        if cycle.cycle_id in self._cycles:
            raise ValueError(f"Cycle {cycle.cycle_id!r} is already stored.")
        self._cycles[cycle.cycle_id] = cycle

    def get(self, cycle_id: str) -> ContributionCycle:
        """Return a cycle or raise KeyError when missing."""
        try:
            return self._cycles[cycle_id]
        except KeyError as exc:
            raise KeyError(f"Cycle {cycle_id!r} was not found.") from exc

    def list(self) -> tuple[ContributionCycle, ...]:
        """Return cycles sorted by stable identifier."""
        return tuple(self._cycles[key] for key in sorted(self._cycles))


class InMemoryMemberRepository:
    """Deterministic in-memory implementation of the member repository."""

    def __init__(self) -> None:
        self._members: dict[str, Member] = {}

    def add(self, member: Member) -> None:
        """Add a member and reject duplicate identifiers."""
        if member.member_id in self._members:
            raise ValueError(f"Member {member.member_id!r} is already stored.")
        self._members[member.member_id] = member

    def get(self, member_id: str) -> Member:
        """Return a member or raise KeyError when missing."""
        try:
            return self._members[member_id]
        except KeyError as exc:
            raise KeyError(f"Member {member_id!r} was not found.") from exc

    def list(self) -> tuple[Member, ...]:
        """Return members sorted by stable identifier."""
        return tuple(self._members[key] for key in sorted(self._members))


class InMemoryClassicRepository:
    """Deterministic in-memory implementation of the Classic repository."""

    def __init__(self) -> None:
        self._rotations: dict[str, ClassicRotation] = {}
        self._payouts: dict[int, ClassicPayout] = {}

    def save_rotation(self, rotation_id: str, rotation: ClassicRotation) -> None:
        """Save a rotation and reject duplicate identifiers."""
        if rotation_id in self._rotations:
            raise ValueError(f"Rotation {rotation_id!r} is already stored.")
        self._rotations[rotation_id] = rotation

    def get_rotation(self, rotation_id: str) -> ClassicRotation:
        """Return a rotation or raise KeyError when missing."""
        try:
            return self._rotations[rotation_id]
        except KeyError as exc:
            raise KeyError(f"Rotation {rotation_id!r} was not found.") from exc

    def record_payout(self, payout: ClassicPayout) -> None:
        """Record a payout and reject duplicate cycle numbers."""
        if payout.cycle_number in self._payouts:
            raise ValueError(f"Cycle {payout.cycle_number} already has a payout.")
        self._payouts[payout.cycle_number] = payout

    def payouts(self) -> tuple[ClassicPayout, ...]:
        """Return payouts sorted by cycle number."""
        return tuple(self._payouts[key] for key in sorted(self._payouts))


class InMemoryGovernanceRepository:
    """Deterministic in-memory storage for governance records."""

    def __init__(self) -> None:
        self._proposals: dict[str, RotationProposal] = {}
        self._rulesets: dict[int, Ruleset] = {}

    def save_proposal(self, proposal: RotationProposal) -> None:
        """Save a proposal and reject duplicate identifiers."""
        if proposal.proposal_id in self._proposals:
            raise ValueError(f"Proposal {proposal.proposal_id!r} is already stored.")
        self._proposals[proposal.proposal_id] = proposal

    def get_proposal(self, proposal_id: str) -> RotationProposal:
        """Return a proposal or raise KeyError when missing."""
        try:
            return self._proposals[proposal_id]
        except KeyError as exc:
            raise KeyError(f"Proposal {proposal_id!r} was not found.") from exc

    def save_ruleset(self, ruleset: Ruleset) -> None:
        """Save a ruleset and reject duplicate versions."""
        if ruleset.version in self._rulesets:
            raise ValueError(f"Ruleset version {ruleset.version} is already stored.")
        self._rulesets[ruleset.version] = ruleset


class InMemoryAuditRepository:
    """Append-only in-memory implementation of the audit repository."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._event_ids: set[str] = set()

    def record(self, event: AuditEvent) -> None:
        """Append an audit event and reject duplicate identifiers."""
        if event.event_id in self._event_ids:
            raise ValueError(f"Audit event {event.event_id!r} is already stored.")
        self._events.append(event)
        self._event_ids.add(event.event_id)

    def all_events(self) -> tuple[AuditEvent, ...]:
        """Return audit events in append order."""
        return tuple(self._events)

    def events_for(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> tuple[AuditEvent, ...]:
        """Return audit history for one aggregate."""
        return tuple(
            event
            for event in self._events
            if event.aggregate_type == aggregate_type
            and event.aggregate_id == aggregate_id
        )


__all__ = [
    "AccountRepository",
    "AuditRepository",
    "ClassicRepository",
    "CycleRepository",
    "GovernanceRepository",
    "GroupRepository",
    "InMemoryAccountRepository",
    "InMemoryCycleRepository",
    "InMemoryGroupRepository",
    "InMemoryMemberRepository",
    "InMemoryClassicRepository",
    "InMemoryGovernanceRepository",
    "InMemoryAuditRepository",
    "LedgerRepository",
    "MemberRepository",
]
