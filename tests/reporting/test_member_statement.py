from decimal import Decimal

from tontine.reporting import (
    ContributionSummary,
    InvestmentSummary,
    PayoutSummary,
    build_member_statement,
)


def test_member_statement_contains_history_outstanding_payouts_and_ownership() -> None:
    statement = build_member_statement(
        member_id="member-a",
        display_name="Mary Jane Doe",
        base_currency="JPY",
        contributions=(
            ContributionSummary(
                "2027-01", Decimal("30000"), Decimal("30000"), "paid", "JPY"
            ),
            ContributionSummary("2027-02", Decimal("30000"), None, "pending", "JPY"),
        ),
        payouts=(PayoutSummary("2027-03", Decimal("150000"), "JPY"),),
        investment=InvestmentSummary(
            units=Decimal("12.5"),
            ownership_percentage=Decimal("25.50"),
            attributable_value=Decimal("1000.25"),
            currency="EUR",
        ),
    )

    assert statement.display_name == "Mary Jane Doe"
    assert statement.base_currency == "JPY"
    assert statement.outstanding_total == Decimal("30000")
    assert statement.payouts[0].amount == Decimal("150000")
    assert statement.investment.units == Decimal("12.5")
    assert statement.investment.currency == "EUR"


def test_member_statement_preserves_fractional_currency_and_penalties() -> None:
    statement = build_member_statement(
        member_id="member-x",
        display_name="Member X",
        base_currency="EUR",
        contributions=(
            ContributionSummary(
                "2027-01", Decimal("100.25"), Decimal("99.75"), "partial", "EUR"
            ),
        ),
        payouts=(),
        investment=InvestmentSummary(Decimal("0"), Decimal("0"), Decimal("0"), "XAF"),
        penalties=Decimal("0.50"),
    )

    assert statement.outstanding_total == Decimal("0.50")
    assert statement.penalties == Decimal("0.50")
    assert statement.investment.currency == "XAF"
