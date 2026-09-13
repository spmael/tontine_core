"""Structured, infrastructure-free member and group reporting objects."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from tontine.currencies import CurrencyCode
from tontine.investments import InvestmentValuation


def _amount(value: Decimal | int | str, label: str) -> Decimal:
    if isinstance(value, float) or not isinstance(value, (Decimal, int, str)):
        raise TypeError(f"{label} must use Decimal-compatible values.")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} must be a valid decimal.") from exc
    if not result.is_finite() or result < 0:
        raise ValueError(f"{label} must be finite and non-negative.")
    return result


@dataclass(frozen=True)
class ContributionSummary:
    """Structured contribution history item for reporting."""

    cycle_id: str
    expected_amount: Decimal
    actual_amount: Decimal | None
    status: str
    currency: CurrencyCode
    penalty: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "expected_amount",
            _amount(self.expected_amount, "Expected contribution"),
        )
        if self.actual_amount is not None:
            object.__setattr__(
                self,
                "actual_amount",
                _amount(self.actual_amount, "Actual contribution"),
            )
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        object.__setattr__(
            self,
            "penalty",
            _amount(self.penalty, "Contribution penalty"),
        )


@dataclass(frozen=True)
class PayoutSummary:
    """Structured payout history item for reporting."""

    cycle_id: str
    amount: Decimal
    currency: CurrencyCode

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", _amount(self.amount, "Payout amount"))
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))


@dataclass(frozen=True)
class InvestmentSummary:
    """Structured member investment ownership summary."""

    units: Decimal
    ownership_percentage: Decimal
    attributable_value: Decimal
    currency: CurrencyCode

    def __post_init__(self) -> None:
        object.__setattr__(self, "units", _amount(self.units, "Investment units"))
        object.__setattr__(
            self,
            "ownership_percentage",
            _amount(self.ownership_percentage, "Ownership percentage"),
        )
        object.__setattr__(
            self,
            "attributable_value",
            _amount(self.attributable_value, "Attributable value"),
        )
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))

    @classmethod
    def from_valuation(
        cls,
        valuation: InvestmentValuation,
        units: Decimal | int | str,
        currency: str,
    ) -> InvestmentSummary:
        """Build ownership and value fields from an investment valuation."""
        normalized_units = _amount(units, "Investment units")
        return cls(
            units=normalized_units,
            ownership_percentage=valuation.member_ownership_percentage(
                normalized_units
            ),
            attributable_value=valuation.member_value(normalized_units),
            currency=CurrencyCode(currency),
        )


@dataclass(frozen=True)
class MemberStatement:
    """Immutable structured statement for one member."""

    member_id: str
    display_name: str
    base_currency: CurrencyCode
    contributions: tuple[ContributionSummary, ...]
    payouts: tuple[PayoutSummary, ...]
    investment: InvestmentSummary
    penalties: Decimal

    @property
    def outstanding_total(self) -> Decimal:
        """Return expected less actual contributions, never below zero."""
        return sum(
            (
                max(
                    item.expected_amount - (item.actual_amount or Decimal("0")),
                    Decimal("0"),
                )
                for item in self.contributions
            ),
            Decimal("0"),
        )

def build_member_statement(
    member_id: str,
    display_name: str,
    base_currency: str,
    contributions: Sequence[ContributionSummary],
    payouts: Sequence[PayoutSummary],
    investment: InvestmentSummary,
    penalties: Decimal | int | str | None = None,
) -> MemberStatement:
    """Build a deterministic member statement from supplied domain records.

    Args:
        member_id: Stable member identifier.
        display_name: Human-readable member name.
        base_currency: Tontine reporting currency.
        contributions: Contribution history records.
        payouts: Historical payout records.
        investment: Units, ownership, and attributable value summary.
        penalties: Optional supplied penalty total. When omitted, it is derived
            from contribution summaries.

    Returns:
        An immutable structured statement; no rendering is performed.
    """
    if not member_id.strip() or not display_name.strip():
        raise ValueError("Member statement identity is required.")
    reporting_currency = CurrencyCode(base_currency)
    if penalties is None and any(
        item.currency != reporting_currency for item in contributions
    ):
        raise ValueError(
            "Contribution penalty currencies must match the base currency."
        )
    return MemberStatement(
        member_id=member_id,
        display_name=display_name,
        base_currency=reporting_currency,
        contributions=tuple(contributions),
        payouts=tuple(payouts),
        investment=investment,
        penalties=_amount(
            sum(
                (item.penalty for item in contributions),
                Decimal("0"),
            )
            if penalties is None
            else penalties,
            "Penalties",
        ),
    )


@dataclass(frozen=True)
class GroupStatement:
    """Immutable structured statement for one group."""

    group_id: str
    base_currency: CurrencyCode
    active_member_ids: tuple[str, ...]
    current_cycle_id: str | None
    expected_contributions: Decimal
    received_contributions: Decimal
    cash_balance: Decimal
    investment_value: Decimal
    liabilities: Decimal
    historical_payouts: tuple[PayoutSummary, ...]
    pending_proposals: tuple[str, ...]
    penalties: Decimal = Decimal("0")

    @property
    def outstanding_contributions(self) -> Decimal:
        """Return expected less received contributions, never below zero."""
        return max(
            self.expected_contributions - self.received_contributions,
            Decimal("0"),
        )

    @property
    def nav(self) -> Decimal:
        """Return cash and investment assets less liabilities."""
        return self.cash_balance + self.investment_value - self.liabilities


def build_group_statement(
    group_id: str,
    base_currency: str,
    active_member_ids: Sequence[str],
    current_cycle_id: str | None,
    expected_contributions: Mapping[str, Decimal | int | str],
    received_contributions: Mapping[str, Decimal | int | str],
    cash_balance: Decimal | int | str,
    investment_value: Decimal | int | str,
    liabilities: Decimal | int | str,
    historical_payouts: Sequence[PayoutSummary],
    pending_proposals: Sequence[str],
    penalties: Decimal | int | str = Decimal("0"),
) -> GroupStatement:
    """Build a deterministic group statement from supplied domain records.

    Args:
        group_id: Stable group identifier.
        active_member_ids: Members active for the statement period.
        current_cycle_id: Current cycle identifier, if one exists.
        expected_contributions: Expected amounts keyed by member ID.
        received_contributions: Received amounts keyed by member ID.
        cash_balance: Ledger-derived cash balance in the base currency.
        investment_value: Investment value in the base currency.
        liabilities: Ledger-derived liabilities in the base currency.
        historical_payouts: Recorded payouts.
        pending_proposals: Governance proposal identifiers awaiting decision.
        penalties: Total assessed penalty amount in the base currency.

    Returns:
        An immutable structured statement; no rendering is performed.
    """
    if not group_id.strip():
        raise ValueError("Group statement identifier is required.")
    return GroupStatement(
        group_id=group_id,
        base_currency=CurrencyCode(base_currency),
        active_member_ids=tuple(active_member_ids),
        current_cycle_id=current_cycle_id,
        expected_contributions=sum(
            (
                _amount(value, "Expected contribution")
                for value in expected_contributions.values()
            ),
            Decimal("0"),
        ),
        received_contributions=sum(
            (
                _amount(value, "Received contribution")
                for value in received_contributions.values()
            ),
            Decimal("0"),
        ),
        cash_balance=_amount(cash_balance, "Cash balance"),
        investment_value=_amount(investment_value, "Investment value"),
        liabilities=_amount(liabilities, "Liabilities"),
        historical_payouts=tuple(historical_payouts),
        pending_proposals=tuple(pending_proposals),
        penalties=_amount(penalties, "Penalties"),
    )


__all__ = [
    "ContributionSummary",
    "GroupStatement",
    "InvestmentSummary",
    "MemberStatement",
    "PayoutSummary",
    "build_group_statement",
    "build_member_statement",
]
