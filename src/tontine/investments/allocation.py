"""Versioned investment allocation rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from tontine._datetime import require_aware_datetime
from tontine.audit import AuditEventRegistry
from tontine.exceptions import MissingRecordError

from ._values import _non_negative


@dataclass(frozen=True)
class AllocationRule:
    """Define allocation percentages without hard-coding investment choices."""

    categories: dict[str, Decimal]

    def __post_init__(self) -> None:
        if not self.categories:
            raise ValueError("At least one allocation category is required.")
        normalized = {
            category.strip(): _non_negative(value, "Allocation percentage")
            for category, value in self.categories.items()
        }
        if any(not category for category in normalized):
            raise ValueError("Allocation category names are required.")
        if sum(normalized.values(), Decimal("0")) != Decimal("100"):
            raise ValueError("Allocation percentages must total 100.")
        object.__setattr__(self, "categories", normalized)

    @property
    def total_percentage(self) -> Decimal:
        """Return the exact Decimal percentage total."""
        return sum(self.categories.values(), Decimal("0"))


@dataclass(frozen=True)
class ScheduledAllocationRule:
    """Immutable allocation-rule version with an effective cycle range."""

    rule_id: str
    version: int
    rule: AllocationRule
    effective_cycle: int
    end_cycle: int | None = None
    cancelled_from_cycle: int | None = None

    def applies_to(self, cycle_number: int) -> bool:
        """Return whether this rule version applies to a cycle."""
        return (
            self.effective_cycle <= cycle_number
            and (self.end_cycle is None or cycle_number <= self.end_cycle)
            and (
                self.cancelled_from_cycle is None
                or cycle_number < self.cancelled_from_cycle
            )
        )


class AllocationRuleSchedule:
    """Resolve recurring, ended, cancelled, and replaced allocation rules."""

    def __init__(self, audit_registry: AuditEventRegistry | None = None) -> None:
        self._rules: list[ScheduledAllocationRule] = []
        self._audit_registry = audit_registry

    def add_rule(
        self,
        rule_id: str,
        version: int,
        rule: AllocationRule,
        effective_cycle: int,
        end_cycle: int | None = None,
        *,
        occurred_at: datetime | None = None,
    ) -> ScheduledAllocationRule:
        """Add a recurring or bounded allocation-rule version.

        Args:
            rule_id: Stable allocation-rule identifier.
            version: Immutable rule version number.
            rule: Percentage allocation definition totaling 100 percent.
            effective_cycle: First cycle using the rule.
            end_cycle: Optional last cycle using the rule.
            occurred_at: Optional timezone-aware occurrence time, constructed
                with ``datetime.timezone.utc`` or ``zoneinfo.ZoneInfo``. When
                omitted, the current local time is used.

        Returns:
            The immutable scheduled rule.

        Raises:
            ValueError: If the rule identity, cycle range, or ``occurred_at`` is
                invalid.
        """
        if occurred_at is not None:
            require_aware_datetime(occurred_at, "occurred_at")
        if not rule_id.strip() or version < 1:
            raise ValueError("Allocation rule identity is invalid.")
        if effective_cycle < 1 or (
            end_cycle is not None and end_cycle < effective_cycle
        ):
            raise ValueError("Allocation rule cycle range is invalid.")
        if any(
            item.rule_id == rule_id and item.version == version for item in self._rules
        ):
            raise ValueError(f"Allocation rule {rule_id!r} is already registered.")
        scheduled = ScheduledAllocationRule(
            rule_id=rule_id,
            version=version,
            rule=rule,
            effective_cycle=effective_cycle,
            end_cycle=end_cycle,
        )
        event_time = occurred_at or datetime.now().astimezone()
        self._rules.append(scheduled)
        self._record_audit("allocation_rule.added", rule_id, version, event_time)
        return scheduled

    def cancel(
        self,
        rule_id: str,
        from_cycle: int,
        *,
        occurred_at: datetime | None = None,
    ) -> None:
        """Stop a recurring rule from a cycle onward without mutating history.

        Args:
            rule_id: Allocation rule to stop.
            from_cycle: First cycle in which the rule no longer applies.
            occurred_at: Optional timezone-aware occurrence time, constructed
                with ``datetime.timezone.utc`` or ``zoneinfo.ZoneInfo``. When
                omitted, the current local time is used.

        Raises:
            MissingRecordError: If the rule is not registered.
            ValueError: If the cancellation cycle is not after activation or
                ``occurred_at`` is naive.
        """
        if occurred_at is not None:
            require_aware_datetime(occurred_at, "occurred_at")
        if from_cycle < 1:
            raise ValueError("Cancellation cycle must be positive.")
        candidates = [item for item in self._rules if item.rule_id == rule_id]
        if not candidates:
            raise MissingRecordError(f"Allocation rule {rule_id!r} was not found.")
        current = max(candidates, key=lambda item: item.effective_cycle)
        if from_cycle <= current.effective_cycle:
            raise ValueError("Cancellation must occur after the rule effective cycle.")
        event_time = occurred_at or datetime.now().astimezone()
        self._rules.remove(current)
        self._rules.append(
            ScheduledAllocationRule(
                rule_id=current.rule_id,
                version=current.version,
                rule=current.rule,
                effective_cycle=current.effective_cycle,
                end_cycle=current.end_cycle,
                cancelled_from_cycle=from_cycle,
            )
        )
        self._record_audit(
            "allocation_rule.cancelled", rule_id, current.version, event_time
        )

    def rule_for_cycle(self, cycle_number: int) -> ScheduledAllocationRule:
        """Return the latest applicable rule version for a cycle.

        Args:
            cycle_number: Positive contribution cycle number.

        Returns:
            The latest scheduled rule effective for the cycle.

        Raises:
            MissingRecordError: If no rule is effective for the cycle.
        """
        if cycle_number < 1:
            raise ValueError("Allocation cycle must be positive.")
        applicable = [item for item in self._rules if item.applies_to(cycle_number)]
        if not applicable:
            raise MissingRecordError(
                f"No allocation rule is effective for cycle {cycle_number}."
            )
        return max(applicable, key=lambda item: item.effective_cycle)

    def _record_audit(
        self, event_type: str, rule_id: str, version: int, occurred_at: datetime
    ) -> None:
        if self._audit_registry is None:
            return
        event_number = len(self._audit_registry.all_events()) + 1
        self._audit_registry.record(
            event_id=f"{event_type}:{rule_id}:{version}:{event_number}",
            event_type=event_type,
            aggregate_type="allocation_rule",
            aggregate_id=rule_id,
            occurred_at=occurred_at,
            actor_id=None,
            source_event=None,
            details={"version": version},
        )
