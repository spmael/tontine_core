"""Reusable conformance checks for hybrid allocation repository adapters."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal

import pytest

from tontine.exceptions import MissingRecordError
from tontine.hybrid import (
    HybridAllocation,
    PendingAllocationReason,
    PendingHybridAllocation,
)
from tontine.repositories import AllocationRepository


def assert_allocation_repository_contract(
    repository_factory: Callable[[], AllocationRepository],
) -> None:
    """Run the shared one-record-per-contribution repository contract."""
    repository = repository_factory()
    pending = PendingHybridAllocation(
        allocation_id="allocation-pending",
        contribution_id="contribution-z",
        member_id="member-z",
        cycle_id="cycle-z",
        cycle_number=2,
        rule_version=1,
        payment_order_version=1,
        received_amount=Decimal("100"),
        currency="XAF",
        receipt_date=date(2027, 2, 1),
        pot_amount=Decimal("70"),
        fund_amount=Decimal("30"),
        reason=PendingAllocationReason.NO_VALUATION,
    )
    resolved_first = HybridAllocation(
        allocation_id="allocation-first",
        contribution_id="contribution-a",
        member_id="member-a",
        cycle_id="cycle-a",
        cycle_number=1,
        rule_version=1,
        payment_order_version=1,
        received_amount=Decimal("100"),
        currency="XAF",
        receipt_date=date(2027, 1, 1),
        allocated_on=date(2027, 1, 1),
        valuation_reference=None,
        valuation_date=None,
        unit_price=Decimal("10"),
        pot_amount=Decimal("70"),
        fund_amount=Decimal("30"),
        units_issued=Decimal("3.0000"),
        cash_residual=Decimal("0"),
    )
    repository.add(pending)
    repository.add(resolved_first)

    assert repository.get(pending.contribution_id) is pending
    with pytest.raises(FrozenInstanceError):
        setattr(pending, "member_id", "changed-member")
    assert [item.contribution_id for item in repository.list()] == [
        "contribution-a",
        "contribution-z",
    ]
    with pytest.raises(MissingRecordError):
        repository.get("missing-contribution")
    with pytest.raises(ValueError, match="already"):
        repository.add(
            PendingHybridAllocation(
                allocation_id="allocation-duplicate",
                contribution_id=pending.contribution_id,
                member_id=pending.member_id,
                cycle_id=pending.cycle_id,
                cycle_number=pending.cycle_number,
                rule_version=pending.rule_version,
                payment_order_version=pending.payment_order_version,
                received_amount=pending.received_amount,
                currency=pending.currency,
                receipt_date=pending.receipt_date,
                pot_amount=pending.pot_amount,
                fund_amount=pending.fund_amount,
                reason=pending.reason,
            )
        )
    assert repository.get(pending.contribution_id) is pending

    resolved_pending = HybridAllocation(
        allocation_id=pending.allocation_id,
        contribution_id=pending.contribution_id,
        member_id=pending.member_id,
        cycle_id=pending.cycle_id,
        cycle_number=pending.cycle_number,
        rule_version=pending.rule_version,
        payment_order_version=pending.payment_order_version,
        received_amount=pending.received_amount,
        currency=pending.currency,
        receipt_date=pending.receipt_date,
        allocated_on=pending.receipt_date,
        valuation_reference="valuation-z",
        valuation_date=pending.receipt_date,
        unit_price=Decimal("10"),
        pot_amount=pending.pot_amount,
        fund_amount=pending.fund_amount,
        units_issued=Decimal("3.0000"),
        cash_residual=Decimal("0"),
    )
    invalid_resolution = HybridAllocation(
        allocation_id=resolved_pending.allocation_id,
        contribution_id=resolved_pending.contribution_id,
        member_id="changed-member",
        cycle_id=resolved_pending.cycle_id,
        cycle_number=resolved_pending.cycle_number,
        rule_version=resolved_pending.rule_version,
        payment_order_version=resolved_pending.payment_order_version,
        received_amount=resolved_pending.received_amount,
        currency=resolved_pending.currency,
        receipt_date=resolved_pending.receipt_date,
        allocated_on=resolved_pending.allocated_on,
        valuation_reference=resolved_pending.valuation_reference,
        valuation_date=resolved_pending.valuation_date,
        unit_price=resolved_pending.unit_price,
        pot_amount=resolved_pending.pot_amount,
        fund_amount=resolved_pending.fund_amount,
        units_issued=resolved_pending.units_issued,
        cash_residual=resolved_pending.cash_residual,
    )
    with pytest.raises(ValueError, match="preserve pending provenance"):
        repository.resolve_pending(invalid_resolution)
    assert repository.get(pending.contribution_id) is pending
    repository.resolve_pending(resolved_pending)
    assert repository.get(pending.contribution_id) is resolved_pending
    with pytest.raises(ValueError, match="resolved"):
        repository.resolve_pending(resolved_pending)
    with pytest.raises(MissingRecordError):
        repository.resolve_pending(
            HybridAllocation(
                allocation_id="missing-allocation",
                contribution_id="missing-contribution",
                member_id="member-x",
                cycle_id="cycle-x",
                cycle_number=1,
                rule_version=1,
                payment_order_version=1,
                received_amount=Decimal("1"),
                currency="XAF",
                receipt_date=resolved_first.receipt_date,
                allocated_on=resolved_first.receipt_date,
                valuation_reference=None,
                valuation_date=None,
                unit_price=Decimal("1"),
                pot_amount=Decimal("0"),
                fund_amount=Decimal("1"),
                units_issued=Decimal("1.0000"),
                cash_residual=Decimal("0"),
            )
        )


__all__ = ["assert_allocation_repository_contract"]
