"""Validate provenance and audit consistency for governance snapshots."""

from __future__ import annotations

from tontine.audit import AuditEvent
from tontine.classic import ClassicRotationSchedule

from .models import (
    InvestmentAuthorizationEffect,
    ProposalStatus,
    RotationExceptionEffect,
    RotationOrderEffect,
    RotationProposal,
    Ruleset,
    RulesetActivationEffect,
)


def validate_effect_provenance(
    schedule: ClassicRotationSchedule,
    proposals: tuple[RotationProposal, ...],
    rulesets: tuple[Ruleset, ...],
    events_by_id: dict[str, AuditEvent],
    governance_event_ids: set[str],
) -> None:
    proposals_by_id = {item.proposal_id: item for item in proposals}
    governance_events = tuple(
        events_by_id[event_id] for event_id in governance_event_ids
    )
    initial_event_id = "initial-governance-rotation"
    expected_rotation_events = {
        item.source_event
        for item in schedule.versions
        if item.source_event != initial_event_id
    }
    actual_rotation_events = {
        item.event_id
        for item in governance_events
        if item.event_type == "rotation_approved"
    }
    if actual_rotation_events != expected_rotation_events:
        raise ValueError(
            "Snapshot rotation audit events do not match applied versions."
        )
    expected_exception_events = {item.approval_event_id for item in schedule.exceptions}
    actual_exception_events = {
        item.event_id
        for item in governance_events
        if item.event_type == "rotation_exception_approved"
    }
    if actual_exception_events != expected_exception_events:
        raise ValueError(
            "Snapshot rotation exception audit events do not match applied effects."
        )
    for version in schedule.versions:
        if (
            version.version == 1
            and version.effective_cycle == 1
            and version.source_event == initial_event_id
        ):
            continue
        event = (
            events_by_id.get(version.source_event)
            if version.source_event in governance_event_ids
            else None
        )
        proposal = next(
            (
                item
                for item in proposals
                if item.status is ProposalStatus.APPROVED
                and item.proposal_id == (event.aggregate_id if event else None)
            ),
            None,
        )
        if (
            event is None
            or event.event_type != "rotation_approved"
            or event.aggregate_type != "proposal"
            or proposal is None
            or proposal.effect is None
            or not isinstance(proposal.effect, RotationOrderEffect)
            or proposal.effect.effective_cycle != version.effective_cycle
            or proposal.effect.rotation != version.rotation
        ):
            raise ValueError(
                "Snapshot rotation version has invalid approval provenance."
            )

    for exception in schedule.exceptions:
        event = events_by_id.get(exception.approval_event_id)
        proposal = proposals_by_id.get(exception.proposal_id)
        if (
            event is None
            or exception.approval_event_id not in governance_event_ids
            or event.event_type != "rotation_exception_approved"
            or event.aggregate_id != exception.proposal_id
            or proposal is None
            or proposal.status is not ProposalStatus.APPROVED
            or proposal.effect is None
            or not isinstance(proposal.effect, RotationExceptionEffect)
            or proposal.effect.exception_id != exception.exception_id
            or proposal.effect.cycle_number != exception.cycle_number
            or proposal.effect.recipient_id != exception.recipient_id
        ):
            raise ValueError(
                "Snapshot rotation exception has invalid approval provenance."
            )

    for proposal in proposals:
        if proposal.status is not ProposalStatus.APPROVED:
            continue
        effect = proposal.effect
        if effect is None:
            raise ValueError("Approved snapshot proposal has no typed effect.")
        if isinstance(effect, RotationOrderEffect):
            if not any(
                event.event_type == "rotation_approved"
                and event.aggregate_id == proposal.proposal_id
                and event.event_id
                in {version.source_event for version in schedule.versions}
                for event in governance_events
            ):
                raise ValueError("Approved rotation proposal effect is not applied.")
        elif isinstance(effect, RotationExceptionEffect):
            if not any(
                item.proposal_id == proposal.proposal_id for item in schedule.exceptions
            ):
                raise ValueError("Approved exception proposal effect is not applied.")
        elif isinstance(effect, RulesetActivationEffect):
            ruleset_effect = effect.ruleset
            if ruleset_effect not in rulesets or not any(
                event.event_type == "ruleset_activated"
                and event.aggregate_id == proposal.proposal_id
                and event.details.get("ruleset_id") == ruleset_effect.ruleset_id
                and event.details.get("version") == ruleset_effect.version
                for event in governance_events
            ):
                raise ValueError("Approved ruleset proposal effect is not applied.")
        elif isinstance(effect, InvestmentAuthorizationEffect):
            if not any(
                event.event_type == "investment_authorization_approved"
                and event.aggregate_id == proposal.proposal_id
                for event in governance_events
            ):
                raise ValueError(
                    "Approved investment authorization has no approval event."
                )
        else:
            raise ValueError("Snapshot proposal has an unsupported typed effect.")


def validate_audit_trail(
    proposals: tuple[RotationProposal, ...],
    active_member_ids: tuple[str, ...],
    rulesets: tuple[Ruleset, ...],
    events: tuple[AuditEvent, ...],
) -> None:
    events_by_proposal: dict[str, list[AuditEvent]] = {}
    for event in events:
        if event.aggregate_type == "proposal":
            events_by_proposal.setdefault(event.aggregate_id, []).append(event)

    for proposal in proposals:
        proposal_events = events_by_proposal.get(proposal.proposal_id, [])
        if not any(
            item.event_type == "proposal_created"
            and item.occurred_at == proposal.created_at
            for item in proposal_events
        ):
            raise ValueError("Snapshot proposal is missing its creation audit event.")
        if proposal.opened_at is not None and not any(
            item.event_type == "proposal_opened"
            and item.occurred_at == proposal.opened_at
            for item in proposal_events
        ):
            raise ValueError("Snapshot proposal is missing its opening audit event.")
        audited_votes = {
            item.details.get("member_id"): item.details.get("choice")
            for item in proposal_events
            if item.event_type == "vote_submitted"
        }
        expected_votes = {
            member_id: choice.value for member_id, choice in proposal.votes.items()
        }
        if audited_votes != expected_votes:
            raise ValueError("Snapshot proposal votes do not match audit history.")
        if proposal.evaluation is not None and not any(
            item.event_type == "proposal_evaluated"
            and item.occurred_at == proposal.evaluation.evaluated_at
            and item.details.get("status") == proposal.status.value
            for item in proposal_events
        ):
            raise ValueError("Snapshot proposal is missing its evaluation audit event.")

    membership_events = [
        item
        for item in events
        if item.aggregate_type == "governance"
        and item.aggregate_id == "active_members"
        and item.event_type == "active_members_changed"
    ]
    if membership_events:
        members_value = membership_events[-1].details.get("member_ids", ())
        if not isinstance(members_value, tuple) or any(
            not isinstance(member_id, str) for member_id in members_value
        ):
            raise ValueError("Snapshot membership audit details are invalid.")
        final_members: tuple[str, ...] = members_value
        if final_members != active_member_ids:
            raise ValueError("Snapshot active members do not match audit history.")

    for ruleset in rulesets:
        has_direct_add = any(
            item.event_type == "ruleset_added"
            and item.aggregate_id == ruleset.ruleset_id
            and item.details.get("version") == ruleset.version
            for item in events
        )
        has_approved_activation = any(
            item.event_type == "ruleset_activated"
            and item.details.get("ruleset_id") == ruleset.ruleset_id
            and item.details.get("version") == ruleset.version
            for item in events
        )
        if not has_direct_add and not has_approved_activation:
            raise ValueError("Snapshot ruleset is missing its audit provenance.")
