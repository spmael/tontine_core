"""Immutable investment activity records and their registry."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

from tontine._datetime import require_aware_datetime
from tontine.currencies import CurrencyCode, smallest_unit
from tontine.exceptions import DuplicateInvestmentEventError

from ._values import _decimal_value
from .assets import AssetDefinition
from .fx import FxRate

if TYPE_CHECKING:
    from tontine.governance.models import InvestmentAuthorizationEffect


class InvestmentActivityType(StrEnum):
    """Recorded investment activity categories."""

    PURCHASE = "purchase"
    SALE = "sale"
    INCOME = "income"
    FEE = "fee"


_AUTHORIZABLE_TYPES = frozenset(
    {InvestmentActivityType.PURCHASE, InvestmentActivityType.SALE}
)

# FR-INV-008 / ADR-005: no current activity type gives zero a meaning. Allowing
# zero for a future type is a single entry here plus a test.
_ZERO_AMOUNT_ALLOWED: dict[InvestmentActivityType, bool] = {
    InvestmentActivityType.PURCHASE: False,
    InvestmentActivityType.SALE: False,
    InvestmentActivityType.INCOME: False,
    InvestmentActivityType.FEE: False,
}

# ADR-005: purchases and sales record a strictly positive asset quantity; income
# and fees move value without changing the quantity held.
_UNITS_REQUIRED: dict[InvestmentActivityType, bool] = {
    InvestmentActivityType.PURCHASE: True,
    InvestmentActivityType.SALE: True,
    InvestmentActivityType.INCOME: False,
    InvestmentActivityType.FEE: False,
}

_NON_POSITIVE_GUIDANCE = (
    "record a waiver or cancellation as a note, correct a recorded event with "
    "a reversal of the original, and record unit-only events such as splits, "
    "bonus shares, or write-offs as corporate actions once supported"
)


def _activity_amount(
    value: Decimal | int | str,
    event_type: InvestmentActivityType,
    currency: CurrencyCode,
    label: str,
) -> Decimal:
    amount = _decimal_value(value, f"{label} amount")
    if amount < 0 or (amount == 0 and not _ZERO_AMOUNT_ALLOWED[event_type]):
        raise ValueError(
            f"{label} amount for {event_type.value} must be positive; "
            f"{_NON_POSITIVE_GUIDANCE}."
        )
    minimum = smallest_unit(currency)
    # Reject rather than round: rounding would let 0.4 XAF become a zero record.
    if amount > 0 and minimum is not None and amount < minimum:
        raise ValueError(
            f"{label} amount {amount} is below the smallest {currency} unit "
            f"of {minimum}."
        )
    return amount


def _activity_units(
    value: Decimal | int | str | None,
    event_type: InvestmentActivityType,
) -> Decimal | None:
    if not _UNITS_REQUIRED[event_type]:
        if value is not None:
            raise ValueError(
                f"Units are only recorded for purchases and sales, "
                f"not {event_type.value}."
            )
        return None
    if value is None:
        raise ValueError(
            f"Units are required for {event_type.value}; supply the asset "
            "quantity bought or sold."
        )
    units = _decimal_value(value, "Units")
    if units <= 0:
        raise ValueError(
            f"Units for {event_type.value} must be positive; {_NON_POSITIVE_GUIDANCE}."
        )
    return units


@dataclass(frozen=True)
class DecisionReference:
    """Structured reference to the governance decision authorizing activity."""

    proposal_id: str

    def __post_init__(self) -> None:
        if not self.proposal_id.strip():
            raise ValueError("Decision reference proposal identifier is required.")


class InvestmentAuthorizationLookup(Protocol):
    """Boundary that resolves approved investment authorization decisions.

    ``tontine.governance.GovernanceRegistry`` satisfies this protocol.
    """

    def approved_investment_authorization(
        self, proposal_id: str
    ) -> InvestmentAuthorizationEffect:
        """Return the approved effect or raise if the decision is not usable."""
        ...


@dataclass(frozen=True)
class InvestmentActivity:
    """Immutable investment activity record without execution behavior.

    ``amount`` is the positive payment or fair value in the activity
    ``currency``, recorded gross. ``asset_amount`` is the same
    value in the asset currency: equal to ``amount`` for same-currency activity,
    or the unquantized conversion through ``fx_rate`` otherwise (ADR-005). Both
    must be at least one smallest ISO 4217 unit of their currency.
    ``units`` is the strictly positive asset quantity for purchases and sales,
    and must be omitted for income and fees.
    ``recorded_at`` must be timezone-aware; construct it with
    ``datetime.timezone.utc`` or ``zoneinfo.ZoneInfo``.
    """

    event_id: str
    event_type: InvestmentActivityType
    asset_id: str
    amount: Decimal
    currency: CurrencyCode
    effective_date: date
    recorded_at: datetime
    source: str
    fx_rate: FxRate | None = None
    asset_amount: Decimal | None = None
    authorization: DecisionReference | None = None
    units: Decimal | None = None

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.asset_id.strip():
            raise ValueError("Investment event and asset identifiers are required.")
        if not self.source.strip():
            raise ValueError("Investment activity source is required.")
        require_aware_datetime(self.recorded_at, "recorded_at")
        event_type = InvestmentActivityType(self.event_type)
        object.__setattr__(self, "event_type", event_type)
        currency = CurrencyCode(str(self.currency))
        object.__setattr__(self, "currency", currency)
        amount = _activity_amount(self.amount, event_type, currency, "Activity")
        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "units", _activity_units(self.units, event_type))
        if self.fx_rate is None:
            expected_asset_amount = amount
        else:
            expected_asset_amount = self.fx_rate.convert(amount, currency)
            _activity_amount(
                expected_asset_amount,
                event_type,
                self.fx_rate.counter_currency(currency),
                "Converted asset",
            )
        if self.asset_amount is not None and self.asset_amount != (
            expected_asset_amount
        ):
            raise ValueError("Asset amount does not match the activity conversion.")
        object.__setattr__(self, "asset_amount", expected_asset_amount)
        if self.authorization is not None and event_type not in _AUTHORIZABLE_TYPES:
            raise ValueError("Only purchases and sales may reference a decision.")


class InvestmentActivityRegistry:
    """Store immutable investment activity and reject duplicate event IDs.

    Args:
        authorization_lookup: Optional governance boundary used to validate
            decision references on purchases and sales.
    """

    def __init__(
        self,
        authorization_lookup: InvestmentAuthorizationLookup | None = None,
    ) -> None:
        self._activities: dict[str, InvestmentActivity] = {}
        self._assets: dict[str, AssetDefinition] = {}
        self._authorization_lookup = authorization_lookup

    def record_activity(
        self,
        event_id: str,
        event_type: InvestmentActivityType,
        asset: AssetDefinition,
        amount: Decimal | int | str,
        currency: str,
        effective_date: date,
        recorded_at: datetime,
        source: str,
        *,
        fx_rate: FxRate | None = None,
        authorization: DecisionReference | None = None,
        units: Decimal | int | str | None = None,
    ) -> InvestmentActivity:
        """Record supplied investment activity without executing a transaction.

        Args:
            event_id: Unique investment-event identifier.
            event_type: Purchase, sale, income, or fee category.
            asset: Asset definition associated with the activity.
            amount: Positive Decimal-compatible amount in ``currency``, recorded
                gross of tax or rebates, and at least the currency's smallest
                ISO 4217 unit. Amounts are never rounded (ADR-005).
            currency: ISO 4217 activity currency.
            effective_date: Date on which the activity occurred.
            recorded_at: Timezone-aware timestamp, constructed with
                ``datetime.timezone.utc`` or ``zoneinfo.ZoneInfo``.
            source: Statement or other supplied provenance source.
            fx_rate: Supplied rate for exactly the activity and asset currency
                pair, in either direction; required only for cross-currency
                activity.
            authorization: Optional approved decision for a purchase or sale.
            units: Strictly positive Decimal-compatible asset quantity; required
                for purchases and sales and rejected for income and fees.

        Returns:
            The immutable activity record.

        Raises:
            DuplicateInvestmentEventError: If the event ID already exists.
            MissingRecordError: If the referenced decision does not exist.
            ValueError: If the amount is not positive or is below the smallest
                activity or asset currency unit, purchase or sale units are
                missing or not positive, income or fee units are supplied, the
                asset conflicts with a
                known definition, the currency or FX rate does not match the
                asset, or the decision reference is unusable, mismatched, or
                exceeds its maximum.
        """
        if event_id in self._activities:
            raise DuplicateInvestmentEventError(
                f"Investment event {event_id!r} is already recorded."
            )
        known_asset = self._assets.get(asset.asset_id)
        if known_asset is not None and known_asset != asset:
            raise ValueError(
                f"Asset {asset.asset_id!r} conflicts with its recorded definition."
            )
        activity_currency = CurrencyCode(currency)
        self._validate_fx_rate(activity_currency, asset.currency, fx_rate)
        activity = InvestmentActivity(
            event_id=event_id,
            event_type=event_type,
            asset_id=asset.asset_id,
            amount=_decimal_value(amount, "Activity amount"),
            currency=activity_currency,
            effective_date=effective_date,
            recorded_at=recorded_at,
            source=source,
            fx_rate=fx_rate,
            authorization=authorization,
            units=None if units is None else _decimal_value(units, "Units"),
        )
        if authorization is not None and activity.asset_amount is not None:
            self._validate_authorization(
                authorization.proposal_id, activity, activity.asset_amount, asset
            )
        self._assets[asset.asset_id] = asset
        self._activities[event_id] = activity
        return activity

    def activities(
        self,
        *,
        asset_id: str | None = None,
        activity_type: InvestmentActivityType | str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> tuple[InvestmentActivity, ...]:
        """Return recorded activity matching all supplied filters.

        Date bounds are inclusive on ``effective_date``. Results are ordered by
        effective date, recorded time, then event ID.

        Raises:
            ValueError: If ``start_date`` is after ``end_date``.
        """
        if start_date is not None and end_date is not None and start_date > end_date:
            raise ValueError("Activity start date cannot be after end date.")
        expected_type = (
            None if activity_type is None else InvestmentActivityType(activity_type)
        )
        matches = (
            activity
            for activity in self._activities.values()
            if (asset_id is None or activity.asset_id == asset_id)
            and (expected_type is None or activity.event_type is expected_type)
            and (start_date is None or activity.effective_date >= start_date)
            and (end_date is None or activity.effective_date <= end_date)
        )
        return tuple(
            sorted(
                matches,
                key=lambda item: (item.effective_date, item.recorded_at, item.event_id),
            )
        )

    def authorized_total(self, proposal_id: str) -> Decimal:
        """Return the asset-currency total of activity citing a decision."""
        return sum(
            (
                activity.asset_amount or Decimal("0")
                for activity in self._activities.values()
                if activity.authorization is not None
                and activity.authorization.proposal_id == proposal_id
            ),
            Decimal("0"),
        )

    @staticmethod
    def _validate_fx_rate(
        activity_currency: CurrencyCode,
        asset_currency: CurrencyCode,
        fx_rate: FxRate | None,
    ) -> None:
        if activity_currency == asset_currency:
            if fx_rate is not None:
                raise ValueError("FX rate is only valid for cross-currency activity.")
            return
        if fx_rate is None:
            raise ValueError("Cross-currency activity requires an explicit FX rate.")
        if {fx_rate.base_currency, fx_rate.quote_currency} != {
            activity_currency,
            asset_currency,
        }:
            raise ValueError(
                "FX rate pair must match the activity and asset currencies."
            )

    def _validate_authorization(
        self,
        proposal_id: str,
        activity: InvestmentActivity,
        asset_amount: Decimal,
        asset: AssetDefinition,
    ) -> None:
        if self._authorization_lookup is None:
            raise ValueError("Decision references require an authorization lookup.")
        effect = self._authorization_lookup.approved_investment_authorization(
            proposal_id
        )
        if (
            effect.asset_id != asset.asset_id
            or effect.activity_type != activity.event_type
            or effect.currency != asset.currency
        ):
            raise ValueError(
                f"Decision {proposal_id!r} does not authorize this activity."
            )
        if self.authorized_total(proposal_id) + asset_amount > (effect.max_amount):
            raise ValueError(
                f"Activity exceeds the maximum authorized by {proposal_id!r}."
            )
