import pytest

from tontine.currencies import CurrencyCode
from tontine.exceptions import InvalidCurrencyError
from tontine.groups import CurrencyCode as GroupCurrencyCode


def test_currency_code_normalizes_known_iso_4217_code() -> None:
    currency = CurrencyCode("jpy")

    assert currency == "JPY"
    assert GroupCurrencyCode is CurrencyCode


def test_currency_code_rejects_unknown_iso_4217_code() -> None:
    with pytest.raises(InvalidCurrencyError, match="ISO 4217"):
        CurrencyCode("ZZZ")
