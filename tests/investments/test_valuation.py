from datetime import date
from decimal import Decimal

import pytest

from tontine.investments import InvestmentValuation, Liability, LiabilityRegistry


def test_valuation_calculates_nav_unit_price_and_member_value() -> None:
    valuation = InvestmentValuation(
        assets=Decimal("1000.25"),
        liabilities=Decimal("100.00"),
        units_outstanding=Decimal("9"),
    )

    assert valuation.nav == Decimal("900.25")
    assert Decimal("100") < valuation.unit_price < Decimal("101")
    assert valuation.member_value(Decimal("3")) == valuation.unit_price * 3
    ownership = valuation.member_ownership_percentage(Decimal("3"))
    assert Decimal("33") < ownership < Decimal("34")


def test_valuation_rejects_zero_units_and_negative_values() -> None:
    with pytest.raises(ValueError, match="(?i)units"):
        InvestmentValuation(
            assets=Decimal("100"),
            liabilities=Decimal("0"),
            units_outstanding=Decimal("0"),
        )

    with pytest.raises(ValueError, match="non-negative"):
        InvestmentValuation(
            assets=Decimal("-1"),
            liabilities=Decimal("0"),
            units_outstanding=Decimal("1"),
        )

    valuation = InvestmentValuation(Decimal("100"), Decimal("0"), Decimal("1"))
    with pytest.raises(ValueError, match="non-negative"):
        valuation.member_value(Decimal("-1"))
    with pytest.raises(ValueError, match="non-negative"):
        InvestmentValuation(Decimal("100"), Decimal("-1"), Decimal("1"))

    with pytest.raises(ValueError, match="exceed"):
        valuation.member_ownership_percentage(Decimal("2"))


def test_valuation_aggregates_currency_matched_liabilities() -> None:
    liabilities = LiabilityRegistry()
    liabilities.record(
        Liability("loan-1", Decimal("100"), "JPY", date(2027, 1, 1), "statement")
    )
    liabilities.record(
        Liability("loan-2", Decimal("25"), "JPY", date(2027, 1, 2), "statement")
    )
    liabilities.record(
        Liability("loan-3", Decimal("50"), "USD", date(2027, 1, 2), "statement")
    )

    valuation = InvestmentValuation.from_liabilities(
        Decimal("1000"), liabilities, "JPY", Decimal("10")
    )
    assert valuation.liabilities == Decimal("125")
    assert valuation.nav == Decimal("875")
    with pytest.raises(ValueError, match="already"):
        liabilities.record(
            Liability("loan-1", Decimal("1"), "JPY", date(2027, 1, 3), "statement")
        )
