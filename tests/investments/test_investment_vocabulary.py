from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from tontine.currencies import CurrencyCode
from tontine.investments import (
    AllocationRule,
    AssetCategory,
    AssetDefinition,
    FxRate,
    ManualValuation,
)


def test_allocation_categories_total_one_hundred_percent() -> None:
    allocation = AllocationRule(
        categories={
            "cash_reserve": Decimal("10"),
            "liquid_assets": Decimal("20"),
            "diversified_investments": Decimal("40"),
            "sovereign_bonds": Decimal("30"),
        }
    )

    assert allocation.total_percentage == Decimal("100")


def test_asset_and_manual_valuation_use_explicit_currency_and_source() -> None:
    asset = AssetDefinition(
        asset_id="bond-cameroon-2027",
        name="Cameroon sovereign bond",
        category=AssetCategory.BOND,
        currency="XAF",
    )
    valuation = ManualValuation(
        asset_id=asset.asset_id,
        value=Decimal("1500000"),
        currency=CurrencyCode("XAF"),
        effective_date=date(2027, 1, 31),
        source="treasurer_statement",
    )

    assert asset.currency == "XAF"
    assert valuation.value == Decimal("1500000")
    assert valuation.source == "treasurer_statement"


def test_fx_rate_is_supplied_data_with_timestamp_and_provider_source() -> None:
    rate = FxRate(
        base_currency="EUR",
        quote_currency="XAF",
        rate=Decimal("655.9570"),
        effective_at=datetime(2027, 1, 31, 12, 0, tzinfo=UTC),
        source="ECB_REFERENCE_FIXTURE",
    )

    assert rate.base_currency == CurrencyCode("EUR")
    assert rate.quote_currency == CurrencyCode("XAF")
    assert rate.rate == Decimal("655.9570")
    assert rate.source == "ECB_REFERENCE_FIXTURE"


def test_vocabulary_rejects_invalid_allocations_and_naive_fx_timestamp() -> None:
    with pytest.raises(ValueError, match="100"):
        AllocationRule(categories={"cash": Decimal("99")})

    with pytest.raises(ValueError, match="timezone-aware"):
        FxRate(
            base_currency="EUR",
            quote_currency="JPY",
            rate=Decimal("160.25"),
            effective_at=datetime(2027, 1, 31, 12, 0),
            source="fixture",
        )
