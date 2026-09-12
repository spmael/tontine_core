from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from tontine.investments import FxRate, is_rate_current


def test_fx_provider_boundary_accepts_supplied_rate_records() -> None:
    rate = FxRate(
        base_currency="EUR",
        quote_currency="XAF",
        rate=Decimal("655.9570"),
        effective_at=datetime(2027, 1, 31, 12, 0, tzinfo=UTC),
        source="ECB_FIXTURE",
    )

    assert isinstance(rate, FxRate)
    assert is_rate_current(
        rate,
        datetime(2027, 1, 31, 13, 0, tzinfo=UTC),
        timedelta(hours=2),
    )


def test_fx_rate_policy_rejects_stale_records() -> None:
    rate = FxRate(
        base_currency="EUR",
        quote_currency="JPY",
        rate=Decimal("160.25"),
        effective_at=datetime(2027, 1, 1, 12, 0, tzinfo=UTC),
        source="ECB_FIXTURE",
    )

    assert not is_rate_current(
        rate,
        datetime(2027, 1, 2, 12, 0, tzinfo=UTC),
        timedelta(hours=2),
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        is_rate_current(rate, datetime(2027, 1, 1, 13, 0), timedelta(hours=2))
