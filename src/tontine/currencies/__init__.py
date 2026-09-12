"""ISO 4217 currency-code value objects."""

from __future__ import annotations

import pycountry

from tontine.exceptions import InvalidCurrencyError


class CurrencyCode(str):
    """Validated and normalized ISO 4217 alpha-3 currency code."""

    def __new__(cls, value: str) -> CurrencyCode:
        code = value.strip().upper()
        if pycountry.currencies.get(alpha_3=code) is None:
            raise InvalidCurrencyError(
                f"Invalid ISO 4217 alpha-3 currency code: {value!r}."
            )
        return str.__new__(cls, code)


__all__ = ["CurrencyCode"]
