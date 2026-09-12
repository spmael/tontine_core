from datetime import UTC, datetime

import pytest

from tontine.audit import AuditEventRegistry
from tontine.exceptions import DuplicateAuditEventError


def test_audit_registry_records_cross_capability_events_in_order() -> None:
    registry = AuditEventRegistry()
    recorded_at = datetime(2027, 1, 15, 12, 0, tzinfo=UTC)

    registry.record(
        event_id="audit-1",
        event_type="contribution.recorded",
        aggregate_type="contribution",
        aggregate_id="contribution-1",
        occurred_at=recorded_at,
        actor_id="treasurer-1",
        source_event="payment-1",
        details={"amount": "30000", "currency": "JPY"},
    )
    registry.record(
        event_id="audit-2",
        event_type="ledger.posted",
        aggregate_type="journal",
        aggregate_id="journal-1",
        occurred_at=recorded_at,
        actor_id="treasurer-1",
        source_event="contribution-1",
        details={"currency": "JPY"},
    )
    registry.record(
        event_id="audit-3",
        event_type="contribution.corrected",
        aggregate_type="contribution",
        aggregate_id="contribution-1",
        occurred_at=recorded_at,
        actor_id="treasurer-1",
        source_event="adjustment-1",
        details={"reason": "correction"},
    )

    events = registry.all_events()
    contribution_events = registry.events_for("contribution", "contribution-1")

    assert [event.event_id for event in events] == ["audit-1", "audit-2", "audit-3"]
    assert [event.event_type for event in contribution_events] == [
        "contribution.recorded",
        "contribution.corrected",
    ]
    assert events[0].details == {"amount": "30000", "currency": "JPY"}


def test_audit_registry_rejects_duplicate_ids_and_naive_timestamps() -> None:
    registry = AuditEventRegistry()
    event_args = {
        "event_id": "audit-1",
        "event_type": "vote.submitted",
        "aggregate_type": "proposal",
        "aggregate_id": "proposal-1",
        "occurred_at": datetime(2027, 1, 15, 12, 0, tzinfo=UTC),
        "actor_id": "member-1",
        "source_event": "vote-1",
        "details": {},
    }
    registry.record(**event_args)

    with pytest.raises(DuplicateAuditEventError):
        registry.record(**event_args)

    with pytest.raises(ValueError, match="timezone-aware"):
        registry.record(
            **{
                **event_args,
                "event_id": "audit-2",
                "occurred_at": datetime(2027, 1, 15, 12, 0),
            }
        )
