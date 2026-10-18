"""Shared Decimal validation for investment values."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation


def _decimal_value(value: Decimal | int | str, label: str) -> Decimal:
    if isinstance(value, float) or not isinstance(value, (Decimal, int, str)):
        raise TypeError(f"{label} must use Decimal-compatible values.")
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} must be a valid decimal.") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{label} must be finite.")
    return decimal_value


def _non_negative(value: Decimal | int | str, label: str) -> Decimal:
    decimal_value = _decimal_value(value, label)
    if decimal_value < 0:
        raise ValueError(f"{label} must be non-negative.")
    return decimal_value
