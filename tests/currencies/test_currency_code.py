from decimal import Decimal

import pytest

from tontine.currencies import CurrencyCode, smallest_unit
from tontine.exceptions import InvalidCurrencyError
from tontine.groups import CurrencyCode as GroupCurrencyCode


def test_currency_code_normalizes_known_iso_4217_code() -> None:
    currency = CurrencyCode("jpy")

    assert currency == "JPY"
    assert GroupCurrencyCode is CurrencyCode


def test_currency_code_rejects_unknown_iso_4217_code() -> None:
    with pytest.raises(InvalidCurrencyError, match="ISO 4217"):
        CurrencyCode("ZZZ")


@pytest.mark.parametrize(
    ("currency", "unit"),
    [
        ("XAF", Decimal("1")),
        ("xof", Decimal("1")),
        ("JPY", Decimal("1")),
        ("EUR", Decimal("0.01")),
        ("USD", Decimal("0.01")),
        ("KWD", Decimal("0.001")),
        ("CLF", Decimal("0.0001")),
    ],
)
def test_smallest_unit_follows_iso_4217_minor_units(
    currency: str, unit: Decimal
) -> None:
    assert smallest_unit(currency) == unit


def test_smallest_unit_is_none_for_codes_without_minor_unit() -> None:
    assert smallest_unit("XAU") is None
    assert smallest_unit("XDR") is None


def test_smallest_unit_rejects_unknown_currency() -> None:
    with pytest.raises(InvalidCurrencyError):
        smallest_unit("ZZZ")
