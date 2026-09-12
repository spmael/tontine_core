from decimal import Decimal

from tontine.reporting import (
    ContributionSummary,
    InvestmentSummary,
    PayoutSummary,
    build_group_statement,
    build_member_statement,
)


def test_summary_projections_preserve_currency_precision() -> None:
    member = build_member_statement(
        member_id="member-eur",
        display_name="EUR Member",
        base_currency="EUR",
        contributions=(
            ContributionSummary(
                "2027-01", Decimal("100.25"), Decimal("100.10"), "partial", "EUR"
            ),
        ),
        payouts=(),
        investment=InvestmentSummary(
            Decimal("2"), Decimal("10"), Decimal("100.25"), "EUR"
        ),
    )
    group = build_group_statement(
        group_id="group-xaf",
        base_currency="XAF",
        active_member_ids=("member-xaf",),
        current_cycle_id="2027-01",
        expected_contributions={"member-xaf": Decimal("30000")},
        received_contributions={"member-xaf": Decimal("30000")},
        cash_balance=Decimal("30000"),
        investment_value=Decimal("0"),
        liabilities=Decimal("0"),
        historical_payouts=(PayoutSummary("2027-01", Decimal("30000"), "XAF"),),
        pending_proposals=(),
    )

    assert member.outstanding_total == Decimal("0.15")
    assert member.investment.currency == "EUR"
    assert group.nav == Decimal("30000")
    assert group.historical_payouts[0].currency == "XAF"
