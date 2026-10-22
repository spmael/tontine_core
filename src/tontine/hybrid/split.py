"""Hybrid contribution split calculations."""

from __future__ import annotations

from decimal import ROUND_DOWN, Decimal, InvalidOperation, localcontext

from tontine.currencies import CurrencyCode, smallest_unit


def split_contribution(
    received: Decimal | int | str,
    currency: str,
    fund_share_bps: int,
) -> tuple[Decimal, Decimal]:
    """Split received cash into ``(pot, fund)`` amounts in currency units.

    The fund share is rounded down to the currency's smallest ISO 4217 unit;
    the pot receives the exact remainder. Expected contributions are not used
    or posted.

    Args:
        received: Amount actually received, as Decimal-compatible input.
        currency: ISO 4217 alpha-3 currency code.
        fund_share_bps: Fund share in basis points, from 0 through 10,000.

    Returns:
        A tuple containing the pot amount followed by the fund amount.

    Raises:
        TypeError: If the amount or basis-point value has an unsupported type.
        ValueError: If the amount is non-finite, negative, below one minor unit,
            or if the basis-point value is outside its permitted range.
        InvalidCurrencyError: If the currency code is unknown.
    """
    if isinstance(received, bool) or not isinstance(received, (Decimal, int, str)):
        raise TypeError("Received amount must use Decimal-compatible values.")
    try:
        amount = Decimal(str(received))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Received amount must be a valid decimal.") from exc
    if not amount.is_finite():
        raise ValueError("Received amount must be finite.")
    if amount < 0:
        raise ValueError("Received amount must not be negative.")

    if type(fund_share_bps) is not int:
        raise TypeError("Fund share in basis points must be an integer.")
    if not 0 <= fund_share_bps <= 10_000:
        raise ValueError("Fund share in basis points must be between 0 and 10,000.")

    code = CurrencyCode(currency)
    minor_unit = smallest_unit(code)
    if minor_unit is None:
        raise ValueError(
            "Contribution splits require a currency with an ISO minor unit."
        )
    if amount < minor_unit:
        raise ValueError(
            f"Received amount {amount} is below the smallest {code} unit "
            f"of {minor_unit}."
        )

    exponent = amount.as_tuple().exponent
    if not isinstance(exponent, int):
        raise ValueError("Received amount must be finite.")
    precision = len(amount.as_tuple().digits) + abs(exponent) + 10
    with localcontext() as context:
        context.prec = max(context.prec, precision)
        fund = (amount * fund_share_bps / 10_000).quantize(
            minor_unit, rounding=ROUND_DOWN
        )
        pot = amount - fund
    return pot, fund
