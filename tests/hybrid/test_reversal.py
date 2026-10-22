from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from tontine.contributions import ContributionCycle
from tontine.exceptions import MissingRecordError
from tontine.hybrid import (
    AllocationReversal,
    HybridAllocation,
    HybridAllocationRegistry,
    HybridRule,
    HybridRuleVersion,
)
from tontine.investments import MemberUnitLedger


def recorded_cycle() -> ContributionCycle:
    cycle = ContributionCycle(
        "cycle-1",
        date(2027, 1, 1),
        date(2027, 1, 15),
        "UTC",
    )
    cycle.add_expected_contribution("member-1", Decimal("10000"))
    cycle.record_contribution(
        "member-1",
        Decimal("10000"),
        payment_date=datetime(2027, 1, 15, 12, tzinfo=UTC),
    )
    return cycle


def recorded_rule() -> HybridRuleVersion:
    return HybridRuleVersion(
        1,
        1,
        0,
        HybridRule("XAF", 3000, Decimal("1000"), 30),
    )


def allocate_original(
    registry: HybridAllocationRegistry,
    ledger: MemberUnitLedger,
    cycle: ContributionCycle | None = None,
) -> HybridAllocation:
    result = registry.allocate(
        allocation_id="allocation-1",
        contribution_id="contribution-1",
        cycle=cycle or recorded_cycle(),
        member_id="member-1",
        cycle_number=1,
        rule_version=recorded_rule(),
        valuations=(),
        unit_ledger=ledger,
    )
    assert isinstance(result, HybridAllocation)
    return result


def reverse(
    registry: HybridAllocationRegistry,
    ledger: MemberUnitLedger,
    *,
    reversal_id: str = "reversal-1",
    recorded_at: datetime = datetime(2027, 1, 20, 12, tzinfo=UTC),
) -> AllocationReversal:
    return registry.reverse(
        "allocation-1",
        reversal_id=reversal_id,
        reason="Receipt was recorded incorrectly",
        recorded_at=recorded_at,
        unit_ledger=ledger,
    )


def test_reversal_links_original_and_offsets_every_value_without_repricing() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    original = allocate_original(registry, ledger)

    reversal = reverse(registry, ledger)

    assert reversal.original_allocation_id == original.allocation_id
    assert reversal.contribution_id == original.contribution_id
    assert reversal.member_id == original.member_id
    assert reversal.reason == "Receipt was recorded incorrectly"
    assert reversal.unit_price == original.unit_price
    assert reversal.pot_offset == -original.pot_amount
    assert reversal.fund_offset == -original.fund_amount
    assert reversal.units_offset == -original.units_issued
    assert reversal.cash_residual_offset == -original.cash_residual
    assert reversal.recorded_at == datetime(2027, 1, 20, 12, tzinfo=UTC)
    assert registry.allocation_for(original.contribution_id) is original
    assert registry.reversal_for(original.allocation_id) is reversal
    assert ledger.balance_for(original.member_id) == Decimal("0")
    assert original.pot_amount + reversal.pot_offset == 0
    assert original.fund_amount + reversal.fund_offset == 0


def test_second_reversal_of_allocation_is_rejected() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    allocate_original(registry, ledger)
    reverse(registry, ledger)

    with pytest.raises(ValueError, match="already has a reversal"):
        reverse(registry, ledger, reversal_id="reversal-2")


def test_reversal_rejects_unknown_allocation() -> None:
    with pytest.raises(MissingRecordError, match="was not found"):
        HybridAllocationRegistry().reverse(
            "missing",
            reversal_id="reversal-1",
            reason="Correction",
            recorded_at=datetime(2027, 1, 20, tzinfo=UTC),
            unit_ledger=MemberUnitLedger(),
        )


def test_corrected_contribution_can_be_allocated_after_reversal() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    cycle = recorded_cycle()
    allocate_original(registry, ledger, cycle)
    reverse(registry, ledger)

    cycle.record_contribution(
        "member-1",
        Decimal("12000"),
        payment_date=datetime(2027, 1, 16, 12, tzinfo=UTC),
        adjustment=True,
    )
    corrected = registry.allocate(
        allocation_id="allocation-2",
        contribution_id="contribution-2",
        cycle=cycle,
        member_id="member-1",
        cycle_number=1,
        rule_version=recorded_rule(),
        valuations=(),
        unit_ledger=ledger,
    )

    assert isinstance(corrected, HybridAllocation)
    assert corrected.received_amount == Decimal("12000")
    assert corrected.units_issued == Decimal("3.6000")
    assert registry.allocations() == (
        registry.allocation_for("contribution-1"),
        corrected,
    )
    assert ledger.balance_for("member-1") == corrected.units_issued


def test_zero_unit_allocation_is_reversed_without_issuing_zero_units() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    version = HybridRuleVersion(
        1,
        1,
        0,
        HybridRule("XAF", 0, Decimal("1000"), 30),
    )
    allocation = registry.allocate(
        allocation_id="allocation-1",
        contribution_id="contribution-1",
        cycle=recorded_cycle(),
        member_id="member-1",
        cycle_number=1,
        rule_version=version,
        valuations=(),
        unit_ledger=ledger,
    )
    assert isinstance(allocation, HybridAllocation)

    reversal = reverse(registry, ledger)

    assert reversal.pot_offset == Decimal("-10000")
    assert reversal.fund_offset == Decimal("0")
    assert reversal.units_offset == Decimal("0")
    assert ledger.total_units == 0


def test_failed_unit_cancellation_does_not_consume_reversal_identifier() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    original = allocate_original(registry, ledger)
    ledger.redeem(original.member_id, Decimal("2"), "prior-redemption")

    with pytest.raises(ValueError, match="cannot exceed"):
        reverse(registry, ledger)

    ledger.issue_units(original.member_id, Decimal("2"), "restored-units")
    reversal = reverse(registry, ledger)
    assert reversal.reversal_id == "reversal-1"
    assert ledger.balance_for(original.member_id) == 0


def test_allocation_and_reversal_identifiers_cannot_collide() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    original = allocate_original(registry, ledger)
    reverse(registry, ledger)
    cycle = recorded_cycle()

    with pytest.raises(ValueError, match="already has an allocation"):
        registry.allocate(
            allocation_id="reversal-1",
            contribution_id="contribution-2",
            cycle=cycle,
            member_id=original.member_id,
            cycle_number=1,
            rule_version=recorded_rule(),
            valuations=(),
            unit_ledger=ledger,
        )


def test_reversal_requires_reason_and_aware_timestamp() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    allocate_original(registry, ledger)

    with pytest.raises(ValueError, match="Reversal reason is required"):
        registry.reverse(
            "allocation-1",
            reversal_id="reversal-1",
            reason=" ",
            recorded_at=datetime(2027, 1, 20, tzinfo=UTC),
            unit_ledger=ledger,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        reverse(
            registry,
            ledger,
            recorded_at=datetime(2027, 1, 20),
        )


def test_replayed_reversal_uses_original_recorded_offsets() -> None:
    source_registry = HybridAllocationRegistry()
    source_ledger = MemberUnitLedger()
    original = allocate_original(source_registry, source_ledger)
    recorded_reversal = reverse(source_registry, source_ledger)

    restored_registry = HybridAllocationRegistry()
    restored_ledger = MemberUnitLedger()
    restored_registry.replay(original, restored_ledger)
    restored_registry.replay_reversal(recorded_reversal, restored_ledger)

    assert restored_registry.reversal_for(original.allocation_id) == recorded_reversal
    assert restored_ledger.balance_for(original.member_id) == 0
    with pytest.raises(ValueError, match="already has a reversal"):
        restored_registry.replay_reversal(recorded_reversal, restored_ledger)


def test_replay_rejects_reversal_with_changed_offsets() -> None:
    source_registry = HybridAllocationRegistry()
    source_ledger = MemberUnitLedger()
    original = allocate_original(source_registry, source_ledger)
    reversal = reverse(source_registry, source_ledger)

    restored_registry = HybridAllocationRegistry()
    restored_registry.replay(original, MemberUnitLedger())
    tampered = AllocationReversal(
        reversal_id="reversal-tampered",
        original_allocation_id=original.allocation_id,
        contribution_id=reversal.contribution_id,
        member_id=reversal.member_id,
        reason=reversal.reason,
        recorded_at=reversal.recorded_at,
        currency=reversal.currency,
        unit_price=reversal.unit_price,
        pot_offset=reversal.pot_offset + Decimal("1"),
        fund_offset=reversal.fund_offset,
        units_offset=reversal.units_offset,
        cash_residual_offset=reversal.cash_residual_offset,
    )

    with pytest.raises(ValueError, match="exactly offset"):
        restored_registry.replay_reversal(tampered, MemberUnitLedger())
