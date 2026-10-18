"""Investment asset definitions and manually supplied valuations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from tontine.currencies import CurrencyCode

from ._values import _non_negative


class AssetCategory(StrEnum):
    """Configurable categories for investment assets."""

    CASH = "cash"
    BOND = "bond"
    EQUITY = "equity"
    FUND = "fund"
    REAL_ESTATE = "real_estate"
    OTHER = "other"


@dataclass(frozen=True)
class AssetDefinition:
    """Identify an investment asset held or tracked by the group."""

    asset_id: str
    name: str
    category: AssetCategory
    currency: CurrencyCode

    def __post_init__(self) -> None:
        if not self.asset_id.strip():
            raise ValueError("Asset identifier is required.")
        if not self.name.strip():
            raise ValueError("Asset name is required.")
        object.__setattr__(self, "category", AssetCategory(self.category))
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))


@dataclass(frozen=True)
class ManualValuation:
    """Record a manually supplied asset valuation with its source."""

    asset_id: str
    value: Decimal
    currency: CurrencyCode
    effective_date: date
    source: str

    def __post_init__(self) -> None:
        if not self.asset_id.strip():
            raise ValueError("Valuation asset identifier is required.")
        if not self.source.strip():
            raise ValueError("Valuation source is required.")
        object.__setattr__(self, "value", _non_negative(self.value, "Valuation"))
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
