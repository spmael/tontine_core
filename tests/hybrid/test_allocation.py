from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from tontine.contributions import ContributionCycle
from tontine.exceptions import MissingRecordError
from tontine.hybrid import (
    ContributionPaymentOrder,
    HybridAllocation,
    HybridAllocationRegistry,
    HybridRule,
    HybridRuleVersion,
    HybridUnitValuation,
    PendingAllocationReason,
    PendingHybridAllocation,
)
from tontine.investments import MemberUnitLedger


def cycle_with_receipt(
    *,
    cycle_id: str = "cycle-1",
    member_id: str = "member-1",
    amount: str = "10000",
    payment_date: datetime = datetime(2027, 1, 15, 12, tzinfo=UTC),
) -> ContributionCycle:
    cycle = ContributionCycle(
        cycle_id=cycle_id,
        start_date=date(2027, 1, 1),
        due_date=date(2027, 1, 15),
        timezone="UTC",
    )
    cycle.add_expected_contribution(member_id, Decimal("10000"))
    cycle.record_contribution(
        member_id,
        Decimal(amount),
        payment_date=payment_date,
    )
    return cycle


def rule_version(
    *,
    fund_share_bps: int = 3000,
    launch_price: str = "1000",
    max_valuation_age_days: int = 30,
    contribution_order: ContributionPaymentOrder = ContributionPaymentOrder.POT_FIRST,
) -> HybridRuleVersion:
    rule = HybridRule(
        currency="XAF",
        fund_share_bps=fund_share_bps,
        launch_unit_price=Decimal(launch_price),
        max_valuation_age_days=max_valuation_age_days,
        contribution_order=contribution_order,
    )
    return HybridRuleVersion(1, 1, 0, rule)


def allocate(
    registry: HybridAllocationRegistry,
    ledger: MemberUnitLedger,
    *,
    contribution_cycle: ContributionCycle | None = None,
    version: HybridRuleVersion | None = None,
    valuations: tuple[HybridUnitValuation, ...] = (),
) -> HybridAllocation | PendingHybridAllocation:
    return registry.allocate(
        allocation_id="allocation-1",
        contribution_id="contribution-1",
        cycle=contribution_cycle or cycle_with_receipt(),
        member_id="member-1",
        cycle_number=1,
        rule_version=version or rule_version(),
        valuations=valuations,
        unit_ledger=ledger,
    )


def valuation(
    valuation_id: str = "valuation-1",
    effective_date: date = date(2027, 1, 15),
    unit_price: str = "333.3333",
) -> HybridUnitValuation:
    return HybridUnitValuation(
        valuation_id=valuation_id,
        effective_date=effective_date,
        unit_price=Decimal(unit_price),
        currency="XAF",
    )


def seed_units(ledger: MemberUnitLedger) -> None:
    ledger.issue_units("existing-member", Decimal("1"), "seed-event")


def test_first_allocation_uses_launch_price_and_records_full_provenance() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()

    result = allocate(registry, ledger, valuations=(valuation(unit_price="500"),))

    assert isinstance(result, HybridAllocation)
    assert result.contribution_id == "contribution-1"
    assert result.member_id == "member-1"
    assert result.cycle_id == "cycle-1"
    assert result.rule_version == result.payment_order_version == 1
    assert result.valuation_reference is None
    assert result.valuation_date is None
    assert result.unit_price == Decimal("1000")
    assert result.pot_amount == Decimal("7000")
    assert result.fund_amount == Decimal("3000")
    assert result.units_issued == Decimal("3.0000")
    assert result.cash_residual == Decimal("0.0000")
    assert result.receipt_date == result.allocated_on == date(2027, 1, 15)
    assert ledger.balance_for("member-1") == result.units_issued


def test_recorded_contribution_can_only_be_allocated_once() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    recorded = cycle_with_receipt()
    allocate(registry, ledger, contribution_cycle=recorded)

    with pytest.raises(ValueError, match="already has an allocation"):
        registry.allocate(
            allocation_id="allocation-2",
            contribution_id="another-id",
            cycle=recorded,
            member_id="member-1",
            cycle_number=1,
            rule_version=rule_version(),
            valuations=(),
            unit_ledger=ledger,
        )


@pytest.mark.parametrize(
    ("amount", "order", "expected_pot", "expected_fund"),
    [
        ("5000", ContributionPaymentOrder.POT_FIRST, "5000", "0"),
        ("8000", ContributionPaymentOrder.POT_FIRST, "7000", "1000"),
        ("5000", ContributionPaymentOrder.PRO_RATA, "3500", "1500"),
    ],
)
def test_partial_receipt_uses_the_versioned_contribution_order(
    amount: str,
    order: ContributionPaymentOrder,
    expected_pot: str,
    expected_fund: str,
) -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    recorded = cycle_with_receipt(amount=amount)

    result = registry.allocate(
        allocation_id="allocation-1",
        contribution_id="contribution-1",
        cycle=recorded,
        member_id="member-1",
        cycle_number=1,
        rule_version=rule_version(contribution_order=order),
        valuations=(),
        unit_ledger=ledger,
    )

    assert isinstance(result, HybridAllocation)
    assert result.pot_amount == Decimal(expected_pot)
    assert result.fund_amount == Decimal(expected_fund)


def test_unrecorded_contribution_cannot_be_allocated() -> None:
    registry = HybridAllocationRegistry()
    cycle = ContributionCycle(
        "cycle-1",
        date(2027, 1, 1),
        date(2027, 1, 15),
        "UTC",
    )
    cycle.add_expected_contribution("member-1", Decimal("10000"))

    with pytest.raises(MissingRecordError, match="No contribution is recorded"):
        allocate(registry, MemberUnitLedger(), contribution_cycle=cycle)


def test_contribution_without_a_payment_timestamp_cannot_be_allocated() -> None:
    cycle = ContributionCycle(
        "cycle-1",
        date(2027, 1, 1),
        date(2027, 1, 15),
        "UTC",
    )
    cycle.add_expected_contribution("member-1", Decimal("10000"))
    cycle.record_contribution("member-1", Decimal("10000"))

    with pytest.raises(ValueError, match="payment date are required"):
        allocate(
            HybridAllocationRegistry(), MemberUnitLedger(), contribution_cycle=cycle
        )


def test_contribution_identity_must_match_its_recording_cycle() -> None:
    cycle = cycle_with_receipt()
    cycle.recorded_contributions["member-1"] = replace(
        cycle.recorded_contributions["member-1"],
        cycle_id="another-cycle",
    )

    with pytest.raises(ValueError, match="identity does not match"):
        allocate(
            HybridAllocationRegistry(), MemberUnitLedger(), contribution_cycle=cycle
        )


def test_no_valuation_with_existing_units_is_held_pending_then_priced_forward() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    seed_units(ledger)

    pending = allocate(registry, ledger)
    assert isinstance(pending, PendingHybridAllocation)
    assert pending.reason is PendingAllocationReason.NO_VALUATION
    assert pending.receipt_date == date(2027, 1, 15)
    assert ledger.balance_for("member-1") == 0

    resolved = registry.resolve_pending(
        "contribution-1",
        allocated_on=date(2027, 1, 20),
        valuations=(valuation(effective_date=date(2027, 1, 18)),),
        unit_ledger=ledger,
    )
    assert isinstance(resolved, HybridAllocation)
    assert resolved.receipt_date == date(2027, 1, 15)
    assert resolved.allocated_on == date(2027, 1, 20)
    assert resolved.valuation_reference == "valuation-1"
    assert resolved.valuation_date == date(2027, 1, 18)
    assert resolved.unit_price == Decimal("333.3333")
    assert resolved.units_issued == Decimal("9.0000")
    assert resolved.cash_residual == Decimal("0.0003000000")
    assert ledger.balance_for("member-1") == resolved.units_issued


def test_pending_contribution_cannot_be_allocated_again() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    seed_units(ledger)
    recorded = cycle_with_receipt()
    pending = allocate(registry, ledger, contribution_cycle=recorded)
    assert isinstance(pending, PendingHybridAllocation)

    with pytest.raises(ValueError, match="already has an allocation"):
        registry.allocate(
            allocation_id="allocation-2",
            contribution_id="contribution-2",
            cycle=recorded,
            member_id="member-1",
            cycle_number=1,
            rule_version=rule_version(),
            valuations=(),
            unit_ledger=ledger,
        )


def test_valuation_on_receipt_date_is_selected_and_future_price_is_ignored() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    seed_units(ledger)

    result = allocate(
        registry,
        ledger,
        valuations=(
            valuation("past", date(2027, 1, 10), "300"),
            valuation("future", date(2027, 1, 16), "500"),
        ),
    )

    assert isinstance(result, HybridAllocation)
    assert result.valuation_reference == "past"
    assert result.unit_price == Decimal("300")


def test_stale_valuation_remains_pending_until_a_fresh_one_exists() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    seed_units(ledger)

    pending = allocate(
        registry,
        ledger,
        contribution_cycle=cycle_with_receipt(
            payment_date=datetime(2027, 3, 1, 12, tzinfo=UTC)
        ),
        valuations=(valuation(effective_date=date(2027, 1, 1)),),
    )

    assert isinstance(pending, PendingHybridAllocation)
    assert pending.reason is PendingAllocationReason.STALE_VALUATION
    still_pending = registry.resolve_pending(
        "contribution-1",
        allocated_on=date(2027, 3, 1),
        valuations=(valuation(effective_date=date(2027, 1, 1)),),
        unit_ledger=ledger,
    )
    assert isinstance(still_pending, PendingHybridAllocation)


def test_units_are_rounded_down_and_residual_remains_as_fund_cash() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    seed_units(ledger)

    result = allocate(
        registry,
        ledger,
        valuations=(valuation(),),
    )

    assert isinstance(result, HybridAllocation)
    assert result.units_issued == Decimal("9.0000")
    assert result.cash_residual == Decimal("0.0003000000")
    assert result.units_issued * result.unit_price + result.cash_residual == (
        result.fund_amount
    )
    assert ledger.balance_for("member-1") == Decimal("9.0000")


def test_zero_fund_share_creates_an_allocation_without_zero_unit_event() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()

    result = allocate(registry, ledger, version=rule_version(fund_share_bps=0))

    assert isinstance(result, HybridAllocation)
    assert result.fund_amount == Decimal("0")
    assert result.units_issued == Decimal("0.0000")
    assert result.cash_residual == Decimal("0")
    assert ledger.total_units == 0
    assert registry.allocation_for("contribution-1") is result


def test_allocation_replay_uses_stored_units_without_resolving_price() -> None:
    original = allocate(HybridAllocationRegistry(), MemberUnitLedger())
    assert isinstance(original, HybridAllocation)

    replay_registry = HybridAllocationRegistry()
    replay_ledger = MemberUnitLedger()
    replay_registry.replay(original, replay_ledger)

    assert replay_registry.allocation_for("contribution-1") == original
    assert replay_ledger.balance_for("member-1") == original.units_issued

    with pytest.raises(ValueError, match="already has an allocation"):
        replay_registry.replay(original, replay_ledger)


@pytest.mark.parametrize(
    ("member_id", "contribution_id", "allocation_id"),
    [
        ("", "contribution-1", "allocation-1"),
        ("member-1", "", "allocation-1"),
        ("member-1", "contribution-1", ""),
    ],
)
def test_allocation_rejects_blank_identifiers(
    member_id: str, contribution_id: str, allocation_id: str
) -> None:
    cycle = cycle_with_receipt()
    if member_id:
        cycle = cycle_with_receipt(member_id=member_id)
    with pytest.raises(ValueError, match="required"):
        HybridAllocationRegistry().allocate(
            allocation_id=allocation_id,
            contribution_id=contribution_id,
            cycle=cycle,
            member_id=member_id,
            cycle_number=1,
            rule_version=rule_version(),
            valuations=(),
            unit_ledger=MemberUnitLedger(),
        )


def test_pending_resolution_rejects_backdating_and_missing_pending_record() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    seed_units(ledger)
    allocate(registry, ledger)

    with pytest.raises(ValueError, match="must not precede"):
        registry.resolve_pending(
            "contribution-1",
            allocated_on=date(2027, 1, 14),
            valuations=(valuation(),),
            unit_ledger=ledger,
        )
    with pytest.raises(MissingRecordError, match="No pending allocation"):
        registry.resolve_pending(
            "missing",
            allocated_on=date(2027, 1, 20),
            valuations=(valuation(),),
            unit_ledger=ledger,
        )


def test_allocation_rejects_rule_not_yet_effective() -> None:
    future = HybridRuleVersion(
        2,
        3,
        1,
        HybridRule("XAF", 3000, Decimal("1000"), 30),
    )
    with pytest.raises(ValueError, match="not effective"):
        allocate(HybridAllocationRegistry(), MemberUnitLedger(), version=future)


def test_valuation_currency_must_match_hybrid_rule() -> None:
    registry = HybridAllocationRegistry()
    ledger = MemberUnitLedger()
    seed_units(ledger)
    eur_valuation = HybridUnitValuation(
        "valuation-eur",
        date(2027, 1, 15),
        Decimal("10"),
        "EUR",
    )

    with pytest.raises(ValueError, match="currency must match"):
        allocate(registry, ledger, valuations=(eur_valuation,))
