"""Append-only, cross-capability audit event records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType

from tontine.exceptions import DuplicateAuditEventError


@dataclass(frozen=True)
class AuditEvent:
    """Immutable audit record for a significant domain event."""

    event_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    occurred_at: datetime
    actor_id: str | None
    source_event: str | None
    details: Mapping[str, object]

    def __post_init__(self) -> None:
        for value, label in (
            (self.event_id, "Audit event identifier"),
            (self.event_type, "Audit event type"),
            (self.aggregate_type, "Audit aggregate type"),
            (self.aggregate_id, "Audit aggregate identifier"),
        ):
            if not value.strip():
                raise ValueError(f"{label} is required.")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("Audit timestamps must be timezone-aware.")
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))


class AuditEventRegistry:
    """Store immutable audit events in deterministic append order."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._event_ids: set[str] = set()

    def record(
        self,
        event_id: str,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        occurred_at: datetime,
        actor_id: str | None,
        source_event: str | None,
        details: Mapping[str, object],
    ) -> AuditEvent:
        """Record an event without requiring a database or external service."""
        if event_id in self._event_ids:
            raise DuplicateAuditEventError(
                f"Audit event {event_id!r} is already recorded."
            )
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            occurred_at=occurred_at,
            actor_id=actor_id,
            source_event=source_event,
            details=details,
        )
        self._events.append(event)
        self._event_ids.add(event_id)
        return event

    def all_events(self) -> tuple[AuditEvent, ...]:
        """Return all events in append order."""
        return tuple(self._events)

    def events_for(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> tuple[AuditEvent, ...]:
        """Return ordered history for one aggregate."""
        return tuple(
            event
            for event in self._events
            if event.aggregate_type == aggregate_type
            and event.aggregate_id == aggregate_id
        )


__all__ = ["AuditEvent", "AuditEventRegistry"]