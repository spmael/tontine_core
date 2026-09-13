from decimal import Decimal

import pytest

from tontine.investments import InvestmentValuation


def test_valuation_calculates_nav_unit_price_and_member_value() -> None:
    valuation = InvestmentValuation(
        assets=Decimal("1000.25"),
        liabilities=Decimal("100.00"),
        units_outstanding=Decimal("9"),
    )

    assert valuation.nav == Decimal("900.25")
    assert Decimal("100") < valuation.unit_price < Decimal("101")
    assert valuation.member_value(Decimal("3")) == valuation.unit_price * 3


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
