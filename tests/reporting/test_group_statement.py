from decimal import Decimal

import pytest

from tontine.reporting import PayoutSummary, build_group_statement


def test_group_statement_derives_contribution_totals_and_nav() -> None:
    statement = build_group_statement(
        group_id="group-1",
        base_currency="JPY",
        active_member_ids=("member-a", "member-b"),
        current_cycle_id="2027-01",
        expected_contributions={
            "member-a": Decimal("30000"),
            "member-b": Decimal("30000"),
        },
        received_contributions={
            "member-a": Decimal("30000"),
            "member-b": Decimal("29900"),
        },
        cash_balance=Decimal("50000"),
        investment_value=Decimal("100000"),
        liabilities=Decimal("5000"),
        historical_payouts=(PayoutSummary("2026-12", Decimal("150000"), "JPY"),),
        pending_proposals=("proposal-1",),
    )

    assert statement.outstanding_contributions == Decimal("100")
    assert statement.nav == Decimal("145000")
    assert statement.historical_payouts[0].amount == Decimal("150000")
    assert statement.pending_proposals == ("proposal-1",)


def test_empty_group_statement_is_deterministic() -> None:
    statement = build_group_statement(
        group_id="group-empty",
        base_currency="XAF",
        active_member_ids=(),
        current_cycle_id=None,
        expected_contributions={},
        received_contributions={},
        cash_balance=Decimal("0"),
        investment_value=Decimal("0"),
        liabilities=Decimal("0"),
        historical_payouts=(),
        pending_proposals=(),
    )

    assert statement.outstanding_contributions == Decimal("0")
    assert statement.nav == Decimal("0")


def test_group_statement_rejects_blank_identity_and_invalid_amounts() -> None:
    arguments = {
        "group_id": "group-1",
        "base_currency": "JPY",
        "active_member_ids": (),
        "current_cycle_id": None,
        "expected_contributions": {},
        "received_contributions": {},
        "cash_balance": Decimal("0"),
        "investment_value": Decimal("0"),
        "liabilities": Decimal("0"),
        "historical_payouts": (),
        "pending_proposals": (),
    }
    with pytest.raises(ValueError, match="identifier"):
        build_group_statement(**{**arguments, "group_id": " "})
    with pytest.raises(ValueError, match="non-negative"):
        build_group_statement(**{**arguments, "cash_balance": Decimal("-1")})
    with pytest.raises(TypeError, match="Decimal-compatible"):
        build_group_statement(**{**arguments, "investment_value": 1.5})
