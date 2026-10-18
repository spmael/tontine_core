"""ISO 4217 currency-code value objects."""

from __future__ import annotations

from decimal import Decimal

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


_DEFAULT_MINOR_UNIT = 2
# ISO 4217 minor-unit exponents that differ from the two-decimal default.
_MINOR_UNIT_EXCEPTIONS: dict[str, int | None] = {
    **dict.fromkeys(
        "BIF CLP DJF GNF ISK JPY KMF KRW PYG RWF UGX UYI VND VUV XAF XOF XPF".split(),
        0,
    ),
    **dict.fromkeys("BHD IQD JOD KWD LYD OMR TND".split(), 3),
    **dict.fromkeys("CLF UYW".split(), 4),
    # Metals, funds, and testing codes have no ISO 4217 minor unit.
    **dict.fromkeys(
        "XAG XAU XBA XBB XBC XBD XDR XPD XPT XSU XTS XUA XXX".split(), None
    ),
}


def smallest_unit(currency: str) -> Decimal | None:
    """Return the smallest ISO 4217 minor unit of a currency.

    For example, ``XAF`` returns ``1``, ``EUR`` returns ``0.01``, and ``KWD``
    returns ``0.001``. This describes settlement granularity only; it does not
    imply that amounts are rounded (ADR-001).

    Args:
        currency: ISO 4217 alpha-3 currency code.

    Returns:
        One minor unit in currency units, or ``None`` when ISO 4217 defines no
        minor unit, as for precious metals and testing codes.

    Raises:
        InvalidCurrencyError: If the currency code is unknown.
    """
    code = CurrencyCode(currency)
    exponent = _MINOR_UNIT_EXCEPTIONS.get(code, _DEFAULT_MINOR_UNIT)
    return None if exponent is None else Decimal(1).scaleb(-exponent)


__all__ = ["CurrencyCode", "smallest_unit"]
