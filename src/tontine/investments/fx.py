"""Supplied FX-rate records and freshness policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Protocol

from tontine._datetime import require_aware_datetime
from tontine.currencies import CurrencyCode

from ._values import _decimal_value


@dataclass(frozen=True)
class FxRate:
    """Record a supplied currency-pair exchange rate.

    ``rate`` is the number of quote-currency units per one base-currency unit.
    ``effective_at`` must be timezone-aware; construct it with
    ``datetime.timezone.utc`` or ``zoneinfo.ZoneInfo``.
    """

    base_currency: CurrencyCode
    quote_currency: CurrencyCode
    rate: Decimal
    effective_at: datetime
    source: str

    def __post_init__(self) -> None:
        base_currency = CurrencyCode(str(self.base_currency))
        quote_currency = CurrencyCode(str(self.quote_currency))
        if base_currency == quote_currency:
            raise ValueError("FX base and quote currencies must differ.")
        if self.rate <= 0:
            raise ValueError("FX rate must be positive.")
        require_aware_datetime(self.effective_at, "effective_at")
        if not self.source.strip():
            raise ValueError("FX rate source is required.")
        object.__setattr__(self, "base_currency", base_currency)
        object.__setattr__(self, "quote_currency", quote_currency)
        object.__setattr__(self, "rate", _decimal_value(self.rate, "FX rate"))

    def convert(self, amount: Decimal, from_currency: str) -> Decimal:
        """Convert an amount into the other currency of this pair.

        Args:
            amount: Decimal amount in ``from_currency`` units.
            from_currency: ISO 4217 code of either side of the pair.

        Returns:
            The unquantized amount in the other currency: multiplied by
            ``rate`` from base to quote, divided by ``rate`` from quote to base.
            No rounding is applied.

        Raises:
            ValueError: If ``from_currency`` is not part of the pair.
        """
        source_currency = CurrencyCode(from_currency)
        if source_currency == self.base_currency:
            return amount * self.rate
        if source_currency == self.quote_currency:
            return amount / self.rate
        raise ValueError("FX rate does not cover the activity currency.")

    def counter_currency(self, currency: str) -> CurrencyCode:
        """Return the other currency of the pair.

        Raises:
            ValueError: If ``currency`` is not part of the pair.
        """
        code = CurrencyCode(currency)
        if code == self.base_currency:
            return self.quote_currency
        if code == self.quote_currency:
            return self.base_currency
        raise ValueError("FX rate does not cover the activity currency.")


class FxRateSource(Protocol):
    """Provider-neutral boundary for externally supplied FX-rate records."""

    def get_rate(
        self,
        base_currency: CurrencyCode,
        quote_currency: CurrencyCode,
        effective_at: datetime,
    ) -> FxRate:
        """Return a supplied FX rate for an aware effective instant.

        Construct ``effective_at`` with ``datetime.timezone.utc`` or
        ``zoneinfo.ZoneInfo``. Implementations may live outside the core.
        """


def is_rate_current(rate: FxRate, as_of: datetime, max_age: timedelta) -> bool:
    """Return whether a supplied rate is within the caller's freshness policy.

    ``as_of`` must be timezone-aware; construct it with ``datetime.timezone.utc``
    or ``zoneinfo.ZoneInfo``.
    """
    require_aware_datetime(as_of, "as_of")
    if max_age < timedelta(0):
        raise ValueError("FX maximum age must be non-negative.")
    return as_of - rate.effective_at <= max_age
