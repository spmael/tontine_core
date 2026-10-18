from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from tontine.audit import AuditEventRegistry
from tontine.exceptions import MissingRecordError
from tontine.investments import AllocationRule, AllocationRuleSchedule


def rule(cash: str) -> AllocationRule:
    return AllocationRule(
        categories={
            "cash": Decimal(cash),
            "investments": Decimal("100") - Decimal(cash),
        }
    )


def test_recurring_rule_is_reused_until_replaced() -> None:
    audit = AuditEventRegistry()
    schedule = AllocationRuleSchedule(audit_registry=audit)
    schedule.add_rule("allocation-v1", 1, rule("10"), effective_cycle=1)
    schedule.add_rule("allocation-v2", 2, rule("20"), effective_cycle=4)

    assert schedule.rule_for_cycle(1).rule_id == "allocation-v1"
    assert schedule.rule_for_cycle(3).rule_id == "allocation-v1"
    assert schedule.rule_for_cycle(4).rule_id == "allocation-v2"
    assert [event.event_type for event in audit.all_events()] == [
        "allocation_rule.added",
        "allocation_rule.added",
    ]
    assert all(event.occurred_at.tzinfo is not None for event in audit.all_events())


def test_rule_can_end_or_be_cancelled_without_mutating_history() -> None:
    schedule = AllocationRuleSchedule()
    original = rule("10")
    schedule.add_rule("allocation-v1", 1, original, effective_cycle=1, end_cycle=3)

    assert schedule.rule_for_cycle(3).rule_id == "allocation-v1"
    with pytest.raises(MissingRecordError):
        schedule.rule_for_cycle(4)
    assert schedule.rule_for_cycle(1).rule is original

    audit = AuditEventRegistry()
    cancellable = AllocationRuleSchedule(audit_registry=audit)
    cancellable.add_rule("allocation-v1", 1, original, effective_cycle=1)
    cancellable.cancel("allocation-v1", from_cycle=3)

    assert cancellable.rule_for_cycle(2).rule_id == "allocation-v1"
    with pytest.raises(MissingRecordError):
        cancellable.rule_for_cycle(3)
    assert all(event.occurred_at.tzinfo is not None for event in audit.all_events())


def test_schedule_mutations_preserve_explicit_audit_times() -> None:
    audit = AuditEventRegistry()
    schedule = AllocationRuleSchedule(audit_registry=audit)
    added_at = datetime(2027, 2, 1, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    cancelled_at = datetime(2027, 2, 2, tzinfo=timezone(timedelta(hours=-4)))

    schedule.add_rule(
        "allocation-timed", 1, rule("10"), effective_cycle=1, occurred_at=added_at
    )
    schedule.cancel("allocation-timed", 3, occurred_at=cancelled_at)

    events = audit.all_events()
    assert events[0].occurred_at is added_at
    assert events[1].occurred_at is cancelled_at


def test_schedule_rejects_naive_occurrence_times_without_mutating_state() -> None:
    audit = AuditEventRegistry()
    schedule = AllocationRuleSchedule(audit_registry=audit)
    naive_time = datetime(2027, 2, 1)
    expected_error = (
        r"occurred_at must be timezone-aware.*datetime\.timezone\.utc.*"
        r"zoneinfo\.ZoneInfo"
    )

    with pytest.raises(ValueError, match=expected_error):
        schedule.add_rule(
            "allocation-naive",
            1,
            rule("10"),
            effective_cycle=1,
            occurred_at=naive_time,
        )
    with pytest.raises(MissingRecordError):
        schedule.rule_for_cycle(1)

    schedule.add_rule("allocation-valid", 1, rule("10"), effective_cycle=1)
    with pytest.raises(ValueError, match=expected_error):
        schedule.cancel("allocation-valid", 3, occurred_at=naive_time)
    assert schedule.rule_for_cycle(2).rule_id == "allocation-valid"
    assert [event.event_type for event in audit.all_events()] == [
        "allocation_rule.added"
    ]


def test_schedule_rejects_duplicate_versions_and_invalid_effective_cycles() -> None:
    schedule = AllocationRuleSchedule()
    schedule.add_rule("allocation-v1", 1, rule("10"), effective_cycle=1)

    with pytest.raises(ValueError, match="already"):
        schedule.add_rule("allocation-v1", 1, rule("20"), effective_cycle=2)
    with pytest.raises(ValueError, match="cycle"):
        schedule.add_rule("allocation-v2", 1, rule("20"), effective_cycle=0)

    with pytest.raises(ValueError, match="identity"):
        schedule.add_rule(" ", 1, rule("20"), effective_cycle=1)
    with pytest.raises(ValueError, match="cycle"):
        schedule.add_rule(
            "allocation-v3", 1, rule("20"), effective_cycle=3, end_cycle=2
        )
    with pytest.raises(ValueError, match="positive"):
        schedule.rule_for_cycle(0)
    with pytest.raises(MissingRecordError, match="not found"):
        schedule.cancel("missing", 2)
    with pytest.raises(ValueError, match="positive"):
        schedule.cancel("allocation-v1", 0)
    with pytest.raises(ValueError, match="after"):
        schedule.cancel("allocation-v1", 1)
