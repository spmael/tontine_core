from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from tontine.investments import (
    AssetCategory,
    AssetDefinition,
    FxRate,
    InvestmentActivity,
    InvestmentActivityRegistry,
    InvestmentActivityType,
)

RECORDED_AT = datetime(2027, 3, 1, 12, 0, tzinfo=UTC)
TESLA = AssetDefinition("tsla", "Tesla", AssetCategory.EQUITY, "USD")
USD_JPY = FxRate("USD", "JPY", Decimal("150"), RECORDED_AT, "central_bank")
JPY_USD = FxRate("JPY", "USD", Decimal("0.0066"), RECORDED_AT, "broker")


def record(
    registry: InvestmentActivityRegistry,
    event_id: str,
    *,
    event_type: str = "purchase",
    asset: AssetDefinition = TESLA,
    amount: str = "100",
    currency: str = "USD",
    effective_date: date = date(2027, 2, 1),
    recorded_at: datetime = RECORDED_AT,
    fx_rate: FxRate | None = None,
    units: str | None = None,
) -> InvestmentActivity:
    if units is None and event_type in {"purchase", "sale"}:
        units = "10"
    return registry.record_activity(
        event_id=event_id,
        event_type=InvestmentActivityType(event_type),
        asset=asset,
        amount=Decimal(amount),
        currency=currency,
        effective_date=effective_date,
        recorded_at=recorded_at,
        source="broker_statement",
        fx_rate=fx_rate,
        units=units,
    )


def test_same_currency_activity_has_matching_asset_amount() -> None:
    activity = record(InvestmentActivityRegistry(), "buy-1")

    assert activity.asset_amount == Decimal("100")
    assert activity.fx_rate is None


def test_cross_currency_fee_keeps_original_amount_rate_and_unrounded_conversion() -> (
    None
):
    fee = record(
        InvestmentActivityRegistry(),
        "fee-1",
        event_type="fee",
        amount="550",
        currency="JPY",
        fx_rate=USD_JPY,
    )

    assert fee.amount == Decimal("550")
    assert fee.currency == "JPY"
    assert fee.fx_rate is USD_JPY
    assert fee.fx_rate.source == "central_bank"
    assert fee.asset_amount == Decimal("550") / Decimal("150")
    assert fee.asset_amount != fee.asset_amount.quantize(Decimal("0.01"))


def test_cross_currency_activity_accepts_rate_in_either_direction() -> None:
    fee = record(
        InvestmentActivityRegistry(),
        "fee-1",
        event_type="fee",
        amount="550",
        currency="JPY",
        fx_rate=JPY_USD,
    )

    assert fee.asset_amount == Decimal("3.6300")


def test_cross_currency_activity_requires_matching_fx_pair() -> None:
    registry = InvestmentActivityRegistry()
    eur_jpy = FxRate("EUR", "JPY", Decimal("160"), RECORDED_AT, "central_bank")

    with pytest.raises(ValueError, match="requires an explicit FX rate"):
        record(registry, "fee-1", event_type="fee", amount="550", currency="JPY")
    with pytest.raises(ValueError, match="pair must match"):
        record(
            registry,
            "fee-2",
            event_type="fee",
            amount="550",
            currency="JPY",
            fx_rate=eur_jpy,
        )
    with pytest.raises(ValueError, match="only valid for cross-currency"):
        record(registry, "buy-1", fx_rate=USD_JPY)
    assert registry.activities() == ()


def test_activity_rejects_inconsistent_supplied_asset_amount() -> None:
    with pytest.raises(ValueError, match="does not match"):
        InvestmentActivity(
            event_id="fee-1",
            event_type=InvestmentActivityType.FEE,
            asset_id="tsla",
            amount=Decimal("550"),
            currency="JPY",
            effective_date=date(2027, 2, 1),
            recorded_at=RECORDED_AT,
            source="broker_statement",
            fx_rate=USD_JPY,
            asset_amount=Decimal("3.67"),
        )


def test_registry_rejects_conflicting_asset_definitions() -> None:
    registry = InvestmentActivityRegistry()
    record(registry, "buy-1")
    relabelled = AssetDefinition("tsla", "Tesla", AssetCategory.EQUITY, "JPY")

    with pytest.raises(ValueError, match="conflicts"):
        record(registry, "buy-2", asset=relabelled, currency="JPY")


def test_activity_queries_filter_inclusively_and_order_deterministically() -> None:
    registry = InvestmentActivityRegistry()
    bond = AssetDefinition("bond-1", "Bond", AssetCategory.BOND, "USD")
    later = datetime(2027, 3, 2, tzinfo=UTC)
    record(registry, "c", effective_date=date(2027, 2, 2))
    record(registry, "b", effective_date=date(2027, 2, 1), recorded_at=later)
    record(registry, "a2", effective_date=date(2027, 2, 1))
    record(registry, "a1", effective_date=date(2027, 2, 1))
    record(registry, "fee", event_type="fee", effective_date=date(2027, 2, 3))
    record(registry, "bond", asset=bond, effective_date=date(2027, 2, 1))

    assert [item.event_id for item in registry.activities(asset_id="tsla")] == [
        "a1",
        "a2",
        "b",
        "c",
        "fee",
    ]
    assert [
        item.event_id
        for item in registry.activities(
            asset_id="tsla",
            activity_type="purchase",
            start_date=date(2027, 2, 2),
            end_date=date(2027, 2, 2),
        )
    ] == ["c"]
    assert [item.event_id for item in registry.activities(activity_type="fee")] == [
        "fee"
    ]
    assert len(registry.activities(end_date=date(2027, 2, 1))) == 4
    with pytest.raises(ValueError, match="start date"):
        registry.activities(start_date=date(2027, 2, 2), end_date=date(2027, 2, 1))


ACTIVITY_TYPES = [item.value for item in InvestmentActivityType]
XAF_BOND = AssetDefinition("bond-xaf", "Bond", AssetCategory.BOND, "XAF")
EUR_FUND = AssetDefinition("fund-eur", "Fund", AssetCategory.FUND, "EUR")
EUR_XAF = FxRate("EUR", "XAF", Decimal("655.957"), RECORDED_AT, "central_bank")


@pytest.mark.parametrize("event_type", ACTIVITY_TYPES)
@pytest.mark.parametrize("amount", ["0", "0.00", "-0", "0E-10"])
def test_zero_amount_is_rejected_for_every_activity_type(
    event_type: str, amount: str
) -> None:
    registry = InvestmentActivityRegistry()

    with pytest.raises(ValueError, match="must be positive"):
        record(registry, "event-1", event_type=event_type, amount=amount)
    assert registry.activities() == ()


@pytest.mark.parametrize("event_type", ACTIVITY_TYPES)
def test_negative_amount_is_rejected_for_every_activity_type(event_type: str) -> None:
    with pytest.raises(ValueError, match="must be positive"):
        record(
            InvestmentActivityRegistry(),
            "event-1",
            event_type=event_type,
            amount="-1",
        )


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-Infinity", "sNaN"])
def test_non_finite_amount_is_rejected(amount: str) -> None:
    with pytest.raises(ValueError, match="finite"):
        InvestmentActivityRegistry().record_activity(
            event_id="buy-1",
            event_type=InvestmentActivityType.PURCHASE,
            asset=TESLA,
            amount=amount,
            currency="USD",
            effective_date=date(2027, 2, 1),
            recorded_at=RECORDED_AT,
            source="broker_statement",
            units="1",
        )


def test_zero_amount_rejection_points_to_the_supported_alternatives() -> None:
    with pytest.raises(ValueError) as error:
        record(InvestmentActivityRegistry(), "fee-1", event_type="fee", amount="0")

    message = str(error.value)
    assert "note" in message
    assert "reversal" in message
    assert "corporate action" in message


def test_zero_amount_policy_covers_every_activity_type() -> None:
    from tontine.investments.activity import _ZERO_AMOUNT_ALLOWED

    assert set(_ZERO_AMOUNT_ALLOWED) == set(InvestmentActivityType)
    assert not any(_ZERO_AMOUNT_ALLOWED.values())


@pytest.mark.parametrize(
    ("asset", "amount"), [(XAF_BOND, "0.001"), (EUR_FUND, "0.001"), (XAF_BOND, "0.4")]
)
def test_amount_below_smallest_currency_unit_is_rejected_not_rounded(
    asset: AssetDefinition, amount: str
) -> None:
    registry = InvestmentActivityRegistry()

    with pytest.raises(ValueError, match=f"below the smallest {asset.currency}"):
        record(registry, "buy-1", asset=asset, amount=amount, currency=asset.currency)
    assert registry.activities() == ()


@pytest.mark.parametrize(
    ("asset", "amount"),
    [(XAF_BOND, "1"), (EUR_FUND, "0.01"), (XAF_BOND, "1.5"), (EUR_FUND, "0.015")],
)
def test_smallest_currency_unit_and_finer_precision_above_it_are_accepted(
    asset: AssetDefinition, amount: str
) -> None:
    activity = record(
        InvestmentActivityRegistry(),
        "buy-1",
        asset=asset,
        amount=amount,
        currency=asset.currency,
    )

    assert activity.amount == Decimal(amount)


def test_converted_asset_amount_below_smallest_asset_unit_is_rejected() -> None:
    registry = InvestmentActivityRegistry()

    with pytest.raises(ValueError, match="Converted asset amount .* smallest EUR"):
        record(
            registry,
            "fee-1",
            event_type="fee",
            asset=EUR_FUND,
            amount="1",
            currency="XAF",
            fx_rate=EUR_XAF,
        )
    assert registry.activities() == ()


def test_converted_asset_amount_at_or_above_smallest_unit_is_accepted() -> None:
    fee = record(
        InvestmentActivityRegistry(),
        "fee-1",
        event_type="fee",
        asset=EUR_FUND,
        amount="7",
        currency="XAF",
        fx_rate=EUR_XAF,
    )

    assert fee.asset_amount == Decimal("7") / Decimal("655.957")


def test_direct_activity_construction_applies_the_same_amount_policy() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        InvestmentActivity(
            event_id="income-1",
            event_type=InvestmentActivityType.INCOME,
            asset_id="tsla",
            amount=Decimal("0"),
            currency="USD",
            effective_date=date(2027, 2, 1),
            recorded_at=RECORDED_AT,
            source="broker_statement",
        )


UNIT_TYPES = ["purchase", "sale"]
VALUE_ONLY_TYPES = ["income", "fee"]


def test_units_policy_covers_every_activity_type() -> None:
    from tontine.investments.activity import _UNITS_REQUIRED

    assert set(_UNITS_REQUIRED) == set(InvestmentActivityType)
    assert {item.value for item, required in _UNITS_REQUIRED.items() if required} == (
        set(UNIT_TYPES)
    )


@pytest.mark.parametrize("event_type", UNIT_TYPES)
@pytest.mark.parametrize("units", ["0.5", "1", "0.0001"])
def test_purchase_and_sale_record_positive_units(event_type: str, units: str) -> None:
    activity = record(
        InvestmentActivityRegistry(), "event-1", event_type=event_type, units=units
    )

    assert activity.units == Decimal(units)


@pytest.mark.parametrize("event_type", UNIT_TYPES)
@pytest.mark.parametrize("units", ["0", "0.00", "-0", "0E-10", "-1"])
def test_non_positive_units_are_rejected_for_purchase_and_sale(
    event_type: str, units: str
) -> None:
    registry = InvestmentActivityRegistry()

    with pytest.raises(ValueError, match=f"Units for {event_type} must be positive"):
        record(registry, "event-1", event_type=event_type, units=units)
    assert registry.activities() == ()


@pytest.mark.parametrize("units", ["NaN", "Infinity", "-Infinity", "sNaN"])
def test_non_finite_units_are_rejected(units: str) -> None:
    with pytest.raises(ValueError, match="Units must be finite"):
        record(InvestmentActivityRegistry(), "buy-1", units=units)


@pytest.mark.parametrize("event_type", UNIT_TYPES)
def test_purchase_and_sale_require_units(event_type: str) -> None:
    with pytest.raises(ValueError, match=f"Units are required for {event_type}"):
        InvestmentActivityRegistry().record_activity(
            event_id="event-1",
            event_type=InvestmentActivityType(event_type),
            asset=TESLA,
            amount=Decimal("100"),
            currency="USD",
            effective_date=date(2027, 2, 1),
            recorded_at=RECORDED_AT,
            source="broker_statement",
        )


@pytest.mark.parametrize("event_type", VALUE_ONLY_TYPES)
def test_income_and_fee_reject_units(event_type: str) -> None:
    with pytest.raises(ValueError, match="only recorded for purchases and sales"):
        record(
            InvestmentActivityRegistry(), "event-1", event_type=event_type, units="1"
        )


def test_non_positive_units_point_to_the_corporate_action_path() -> None:
    with pytest.raises(ValueError, match="corporate action"):
        record(InvestmentActivityRegistry(), "buy-1", units="0")


def test_direct_activity_construction_applies_the_same_units_policy() -> None:
    with pytest.raises(ValueError, match="Units for sale must be positive"):
        InvestmentActivity(
            event_id="sale-1",
            event_type=InvestmentActivityType.SALE,
            asset_id="tsla",
            amount=Decimal("100"),
            currency="USD",
            effective_date=date(2027, 2, 1),
            recorded_at=RECORDED_AT,
            source="broker_statement",
            units=Decimal("0"),
        )
