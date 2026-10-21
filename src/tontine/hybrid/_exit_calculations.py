"""Pure calculations supporting member exit settlement."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from decimal import Decimal

from tontine.classic import ClassicPayout
from tontine.contributions import ContributionCycle
from tontine.currencies import CurrencyCode

from .allocation import HybridUnitValuation
from .exit_models import _currency_amount, _net_amount, _sum_amounts


def first_eligible_valuation(
    valuations: Iterable[HybridUnitValuation],
    exit_date: date,
    available_on: date,
    currency: CurrencyCode,
) -> HybridUnitValuation | None:
    candidates = [
        item
        for item in valuations
        if exit_date <= item.effective_date <= available_on
        and item.currency == currency
    ]
    if len({item.effective_date for item in candidates}) != len(candidates):
        raise ValueError("Valuation history contains duplicate effective dates.")
    return min(candidates, key=lambda item: item.effective_date) if candidates else None


def excess_pot_received(
    member_id: str,
    exit_date: date,
    currency: CurrencyCode,
    contribution_cycles: Iterable[ContributionCycle],
    payouts: Iterable[ClassicPayout],
) -> Decimal:
    cycles = tuple(contribution_cycles)
    if len({cycle.cycle_id for cycle in cycles}) != len(cycles):
        raise ValueError("Contribution history contains duplicate cycles.")
    payout_history = tuple(payouts)
    if len({item.cycle_number for item in payout_history}) != len(payout_history):
        raise ValueError("Payout history contains duplicate cycles.")
    contributions: list[Decimal] = []
    for cycle in cycles:
        contribution = cycle.recorded_contributions.get(member_id)
        if (
            contribution is None
            or contribution.actual_amount is None
            or contribution.payment_date is None
            or contribution.payment_date.date() > exit_date
        ):
            continue
        contributions.append(
            recorded_currency_amount(
                contribution.actual_amount, currency, "Contribution amount"
            )
        )
    received: list[Decimal] = []
    for payout in payout_history:
        if payout.currency != currency:
            raise ValueError("Payout history currency must match the exit currency.")
        if payout.recipient_id == member_id and payout.recorded_at.date() <= exit_date:
            received.append(
                recorded_currency_amount(payout.amount, currency, "Payout amount")
            )
    return max(
        _net_amount(_sum_amounts(*received), _sum_amounts(*contributions)),
        Decimal("0"),
    )


def recorded_currency_amount(
    value: Decimal, currency: CurrencyCode, label: str
) -> Decimal:
    amount = _currency_amount(value, currency)
    if amount != value:
        raise ValueError(f"{label} exceeds {currency} minor-unit precision.")
    return amount


__all__ = ["excess_pot_received", "first_eligible_valuation"]
