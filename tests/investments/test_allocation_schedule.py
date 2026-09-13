from decimal import Decimal

import pytest

from tontine.audit import AuditEventRegistry
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


def test_rule_can_end_or_be_cancelled_without_mutating_history() -> None:
    schedule = AllocationRuleSchedule()
    original = rule("10")
    schedule.add_rule("allocation-v1", 1, original, effective_cycle=1, end_cycle=3)

    assert schedule.rule_for_cycle(3).rule_id == "allocation-v1"
    with pytest.raises(KeyError):
        schedule.rule_for_cycle(4)
    assert schedule.rule_for_cycle(1).rule is original

    cancellable = AllocationRuleSchedule()
    cancellable.add_rule("allocation-v1", 1, original, effective_cycle=1)
    cancellable.cancel("allocation-v1", from_cycle=3)

    assert cancellable.rule_for_cycle(2).rule_id == "allocation-v1"
    with pytest.raises(KeyError):
        cancellable.rule_for_cycle(3)


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
        schedule.add_rule("allocation-v3", 1, rule("20"), effective_cycle=3, end_cycle=2)
    with pytest.raises(ValueError, match="positive"):
        schedule.rule_for_cycle(0)
    with pytest.raises(KeyError, match="not found"):
        schedule.cancel("missing", 2)
    with pytest.raises(ValueError, match="positive"):
        schedule.cancel("allocation-v1", 0)
    with pytest.raises(ValueError, match="after"):
        schedule.cancel("allocation-v1", 1)
