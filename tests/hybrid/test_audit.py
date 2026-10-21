from datetime import UTC, date, datetime
from decimal import Decimal

from tontine.audit import AuditEventRegistry
from tontine.contributions import ContributionCycle
from tontine.hybrid import (
    HybridAllocationRegistry,
    HybridRule,
    HybridRuleVersion,
    HybridUnitValuation,
)
from tontine.investments import MemberUnitLedger


def test_allocation_pending_resolution_and_reversal_emit_stable_audit_events() -> None:
    audit = AuditEventRegistry()
    registry = HybridAllocationRegistry(audit)
    ledger = MemberUnitLedger()
    ledger.issue_units("existing-member", Decimal("1"), "seed")
    cycle = ContributionCycle(
        "cycle-1",
        date(2027, 1, 1),
        date(2027, 1, 31),
        "UTC",
    )
    cycle.add_expected_contribution("member-1", Decimal("100"))
    cycle.record_contribution(
        "member-1",
        Decimal("100"),
        payment_date=datetime(2027, 1, 15, 12, tzinfo=UTC),
    )
    rule_version = HybridRuleVersion(
        1,
        1,
        0,
        HybridRule(
            currency="XAF",
            fund_share_bps=3000,
            launch_unit_price=Decimal("10"),
            max_valuation_age_days=30,
        ),
    )

    pending = registry.allocate(
        allocation_id="allocation-1",
        contribution_id="contribution-1",
        cycle=cycle,
        member_id="member-1",
        cycle_number=1,
        rule_version=rule_version,
        valuations=(),
        unit_ledger=ledger,
    )
    resolved = registry.resolve_pending(
        "contribution-1",
        allocated_on=date(2027, 1, 16),
        valuations=(
            HybridUnitValuation(
                "valuation-1",
                date(2027, 1, 16),
                Decimal("10"),
                "XAF",
            ),
        ),
        unit_ledger=ledger,
    )
    registry.reverse(
        "allocation-1",
        reversal_id="reversal-1",
        reason="Correct the source receipt.",
        recorded_at=datetime(2027, 1, 17, 12, tzinfo=UTC),
        unit_ledger=ledger,
    )

    assert pending.allocation_id == resolved.allocation_id
    events = registry.audit_events("allocation-1")
    assert [event.event_type for event in events] == [
        "hybrid_allocation_pending",
        "hybrid_allocation_resolved",
        "hybrid_allocation_reversed",
    ]
    assert [event.event_id for event in events] == [
        "hybrid-allocation:hybrid_allocation_pending:contribution-1",
        "hybrid-allocation:hybrid_allocation_resolved:contribution-1",
        "hybrid-allocation:hybrid_allocation_reversed:reversal-1",
    ]
    assert events[0].occurred_at == datetime(2027, 1, 15, tzinfo=UTC)
    assert events[2].occurred_at == datetime(2027, 1, 17, 12, tzinfo=UTC)
    assert audit.events_for("hybrid_allocation", "allocation-1") == events
