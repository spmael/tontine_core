"""ISO 3166-1 country-code value objects."""

from __future__ import annotations

import pycountry

from tontine.exceptions import InvalidCountryError


class CountryCode(str):
    """Validated and normalized ISO 3166-1 alpha-2 country code."""

    def __new__(cls, value: str) -> CountryCode:
        code = value.strip().upper()
        if pycountry.countries.get(alpha_2=code) is None:
            raise InvalidCountryError(
                f"Invalid ISO 3166-1 alpha-2 country code: {value!r}."
            )
        return str.__new__(cls, code)


__all__ = ["CountryCode"]