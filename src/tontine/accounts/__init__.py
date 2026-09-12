"""Framework-independent records for external financial accounts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from tontine.countries import CountryCode
from tontine.exceptions import DuplicateAccountError, UnsafeAccountReferenceError
from tontine.groups import CurrencyCode


class FinancialAccountId(str):
    """Strongly typed identifier for a registered financial account."""

    def __new__(cls, value: str) -> FinancialAccountId:
        if not value or not value.strip():
            raise ValueError("Financial account identifier is required.")
        if any(char.isspace() for char in value):
            raise ValueError("Financial account identifier cannot contain whitespace.")
        return str.__new__(cls, value)


class AccountType(StrEnum):
    """Supported categories of external custody locations."""

    CASH = "cash"
    BANK = "bank"
    MICROFINANCE = "microfinance"
    MOBILE_WALLET = "mobile_wallet"
    BROKER = "broker"
    OTHER = "other"


class AccountStatus(StrEnum):
    """Registration status of an external account record."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class AccountEventType(StrEnum):
    """Financial event categories that may reference an account record."""

    CONTRIBUTION = "contribution"
    PAYOUT = "payout"
    CASH_MOVEMENT = "cash_movement"
    INVESTMENT = "investment"


_CREDENTIAL_WORDS = re.compile(
    r"(?i)(password|passphrase|credential|token|secret|api[_ -]?key)"
)
_LONG_DIGIT_SEQUENCE = re.compile(r"\d{8,}")
_MASK_MARKER = re.compile(r"[*xX]")
_INSTITUTIONAL_TYPES = {
    AccountType.BANK,
    AccountType.MICROFINANCE,
    AccountType.MOBILE_WALLET,
    AccountType.BROKER,
}


@dataclass(frozen=True)
class FinancialAccount:
    """Record an external account without connecting to or controlling it."""

    account_id: FinancialAccountId
    display_name: str
    account_type: AccountType
    currency: CurrencyCode
    masked_reference: str
    institution_name: str | None = None
    country: CountryCode | None = None
    custodian_description: str | None = None
    status: AccountStatus = AccountStatus.ACTIVE

    def __post_init__(self) -> None:
        object.__setattr__(self, "account_id", FinancialAccountId(str(self.account_id)))
        object.__setattr__(self, "account_type", AccountType(self.account_type))
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))
        object.__setattr__(self, "status", AccountStatus(self.status))
        if self.country is not None:
            object.__setattr__(self, "country", CountryCode(self.country))
        if not self.display_name.strip():
            raise ValueError("Financial account display name is required.")
        self._validate_institution_metadata()
        self._validate_reference()

    def _validate_institution_metadata(self) -> None:
        if self.account_type not in _INSTITUTIONAL_TYPES:
            return
        if not self.institution_name or not self.institution_name.strip():
            raise ValueError(
                f"{self.account_type.value} accounts require an institution name."
            )
        if self.country is None:
            raise ValueError(
                f"{self.account_type.value} accounts require a country code."
            )

    def _validate_reference(self) -> None:
        reference = self.masked_reference.strip()
        if not reference:
            raise UnsafeAccountReferenceError("Masked account reference is required.")
        if _CREDENTIAL_WORDS.search(reference) or _LONG_DIGIT_SEQUENCE.search(
            reference
        ):
            raise UnsafeAccountReferenceError(
                "Account references cannot contain credentials or unmasked identifiers."
            )
        if not _MASK_MARKER.search(reference):
            raise UnsafeAccountReferenceError(
                "Account references must contain a mask marker such as ****."
            )
        object.__setattr__(self, "masked_reference", reference)


@dataclass(frozen=True)
class AccountEventReference:
    """Reference a recorded financial event to a registered account."""

    event_id: str
    event_type: AccountEventType
    account_id: FinancialAccountId
    event_date: date


class FinancialAccountRegistry:
    """Store account records and reconstruct their event references in memory."""

    def __init__(self) -> None:
        self._accounts: dict[str, FinancialAccount] = {}
        self._events: dict[str, list[AccountEventReference]] = {}
        self._ledger_accounts: dict[str, str] = {}

    def register(self, account: FinancialAccount) -> None:
        """Register an account without contacting the external institution.

        Args:
            account: Validated immutable external-account record.

        Raises:
            DuplicateAccountError: If the account ID is already registered.
        """
        if account.account_id in self._accounts:
            raise DuplicateAccountError(
                f"Account {account.account_id!r} is already registered."
            )
        self._accounts[account.account_id] = account
        self._events[account.account_id] = []

    def get(self, account_id: str) -> FinancialAccount:
        """Return a registered account by identifier.

        Args:
            account_id: Stable financial-account identifier.

        Raises:
            KeyError: If no account has the requested ID.
        """
        try:
            return self._accounts[account_id]
        except KeyError as exc:
            raise KeyError(f"Account {account_id!r} was not found.") from exc

    def record_event(
        self,
        event_id: str,
        event_type: AccountEventType,
        account_id: str,
        event_date: date,
    ) -> AccountEventReference:
        """Record an event reference without processing the underlying event.

        Args:
            event_id: Stable source-event identifier.
            event_type: Contribution, payout, cash-movement, or investment type.
            account_id: Registered account referenced by the event.
            event_date: Date on which the event occurred.

        Returns:
            The immutable account-event reference.
        """
        account = self.get(account_id)
        if account.status is AccountStatus.INACTIVE:
            raise ValueError(f"Account {account_id!r} is inactive.")
        reference = AccountEventReference(
            event_id=event_id,
            event_type=AccountEventType(event_type),
            account_id=account.account_id,
            event_date=event_date,
        )
        self._events[account_id].append(reference)
        return reference

    def events_for(self, account_id: str) -> tuple[AccountEventReference, ...]:
        """Return recorded event references for an account."""
        self.get(account_id)
        return tuple(self._events[account_id])

    def link_ledger_account(self, account_id: str, ledger_account_id: str) -> None:
        """Link an account record to a logical ledger identifier.

        Args:
            account_id: Registered financial-account identifier.
            ledger_account_id: Non-empty logical ledger identifier.
        """
        self.get(account_id)
        if not ledger_account_id or any(char.isspace() for char in ledger_account_id):
            raise ValueError("Logical ledger account identifier is invalid.")
        self._ledger_accounts[account_id] = ledger_account_id

    def ledger_account_for(self, account_id: str) -> str:
        """Return the logical ledger identifier linked to an account."""
        self.get(account_id)
        try:
            return self._ledger_accounts[account_id]
        except KeyError as exc:
            raise KeyError(
                f"No logical ledger account is linked to {account_id!r}."
            ) from exc


__all__ = [
    "AccountEventReference",
    "AccountEventType",
    "AccountStatus",
    "AccountType",
    "FinancialAccount",
    "FinancialAccountId",
    "FinancialAccountRegistry",
]
