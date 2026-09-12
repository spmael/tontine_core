from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from tontine.exceptions import DuplicateInvestmentEventError
from tontine.investments import (
    AssetCategory,
    AssetDefinition,
    InvestmentActivityRegistry,
    InvestmentActivityType,
)


def test_records_purchase_sale_income_and_fee_activity() -> None:
    registry = InvestmentActivityRegistry()
    asset = AssetDefinition("bond-1", "Bond", AssetCategory.BOND, "XAF")
    recorded_at = datetime(2027, 1, 31, 12, 0, tzinfo=UTC)

    purchase = registry.record_activity(
        event_id="purchase-1",
        event_type=InvestmentActivityType.PURCHASE,
        asset=asset,
        amount=Decimal("1000000"),
        currency="XAF",
        effective_date=date(2027, 1, 30),
        recorded_at=recorded_at,
        source="treasurer_statement",
    )
    sale = registry.record_activity(
        event_id="sale-1",
        event_type="sale",
        asset=asset,
        amount=Decimal("1005000"),
        currency="XAF",
        effective_date=date(2027, 2, 15),
        recorded_at=recorded_at,
        source="treasurer_statement",
    )
    income = registry.record_activity(
        event_id="income-1",
        event_type="income",
        asset=asset,
        amount=Decimal("5000"),
        currency="XAF",
        effective_date=date(2027, 2, 15),
        recorded_at=recorded_at,
        source="issuer_statement",
    )
    fee = registry.record_activity(
        event_id="fee-1",
        event_type="fee",
        asset=asset,
        amount=Decimal("100"),
        currency="XAF",
        effective_date=date(2027, 2, 15),
        recorded_at=recorded_at,
        source="broker_statement",
    )

    assert [activity.event_type for activity in (purchase, sale, income, fee)] == [
        InvestmentActivityType.PURCHASE,
        InvestmentActivityType.SALE,
        InvestmentActivityType.INCOME,
        InvestmentActivityType.FEE,
    ]


def test_activity_is_immutable_and_duplicate_events_are_rejected() -> None:
    registry = InvestmentActivityRegistry()
    asset = AssetDefinition("bond-1", "Bond", AssetCategory.BOND, "XAF")
    arguments = {
        "event_id": "purchase-1",
        "event_type": "purchase",
        "asset": asset,
        "amount": Decimal("1000000"),
        "currency": "XAF",
        "effective_date": date(2027, 1, 30),
        "recorded_at": datetime(2027, 1, 31, 12, 0, tzinfo=UTC),
        "source": "statement",
    }
    activity = registry.record_activity(**arguments)

    with pytest.raises(AttributeError):
        activity.amount = Decimal("1")  # type: ignore[misc]
    with pytest.raises(DuplicateInvestmentEventError):
        registry.record_activity(**arguments)
