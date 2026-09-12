"""Immutable ledger vocabulary and journal provenance records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from tontine.currencies import CurrencyCode
from tontine.exceptions import DuplicateJournalError


class LedgerAccountId(str):
    """Strongly typed identifier for a logical ledger account."""

    def __new__(cls, value: str) -> LedgerAccountId:
        if not value or not value.strip():
            raise ValueError("Ledger account identifier is required.")
        if any(char.isspace() for char in value):
            raise ValueError("Ledger account identifier cannot contain whitespace.")
        return str.__new__(cls, value)


class EntryDirection(StrEnum):
    """The accounting side of a ledger entry."""

    DEBIT = "debit"
    CREDIT = "credit"


@dataclass(frozen=True)
class LedgerEntry:
    """One Decimal-denominated debit or credit for a logical account."""

    account_id: LedgerAccountId
    direction: EntryDirection
    amount: Decimal
    currency: CurrencyCode

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError("Ledger amounts must use Decimal.")
        if not self.amount.is_finite():
            raise ValueError("Ledger amount must be finite.")
        if self.amount < 0:
            raise ValueError("Ledger amount must be non-negative.")
        object.__setattr__(self, "account_id", LedgerAccountId(str(self.account_id)))
        object.__setattr__(self, "direction", EntryDirection(self.direction))
        object.__setattr__(self, "currency", CurrencyCode(str(self.currency)))


@dataclass(frozen=True)
class JournalEntry:
    """Immutable journal record with timestamp and source-event provenance."""

    journal_id: str
    recorded_at: datetime
    description: str
    source_event: str
    entries: tuple[LedgerEntry, ...]
    reference: str | None = None
    actor: str | None = None

    def __post_init__(self) -> None:
        if not self.journal_id.strip():
            raise ValueError("Journal identifier is required.")
        if not self.description.strip():
            raise ValueError("Journal description is required.")
        if not self.source_event.strip():
            raise ValueError("Journal source event is required.")
        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("Journal timestamps must be timezone-aware.")
        object.__setattr__(self, "entries", tuple(self.entries))


class InMemoryLedgerRepository:
    """Store posted journals and derive balances from their entries in memory."""

    def __init__(self) -> None:
        self._journals: list[JournalEntry] = []
        self._journal_ids: set[str] = set()

    def post(self, journal: JournalEntry) -> None:
        """Post a balanced journal without maintaining manual balances.

        Args:
            journal: Immutable journal with Decimal entries in one currency.

        Raises:
            DuplicateJournalError: If the journal identifier is already posted.
            ValueError: If entries are missing a debit or credit, use mixed
                currencies, or do not balance.
        """
        if journal.journal_id in self._journal_ids:
            raise DuplicateJournalError(
                f"Journal {journal.journal_id!r} is already posted."
            )
        if not any(
            entry.direction is EntryDirection.DEBIT for entry in journal.entries
        ):
            raise ValueError("A journal requires debit and credit entries.")
        if not any(
            entry.direction is EntryDirection.CREDIT for entry in journal.entries
        ):
            raise ValueError("A journal requires debit and credit entries.")
        currencies = {entry.currency for entry in journal.entries}
        if len(currencies) != 1:
            raise ValueError("All entries in a journal must use one currency.")
        debit_total = sum(
            (
                entry.amount
                for entry in journal.entries
                if entry.direction is EntryDirection.DEBIT
            ),
            Decimal("0"),
        )
        credit_total = sum(
            (
                entry.amount
                for entry in journal.entries
                if entry.direction is EntryDirection.CREDIT
            ),
            Decimal("0"),
        )
        if debit_total != credit_total:
            raise ValueError("Journal debit and credit totals must balance.")
        self._journals.append(journal)
        self._journal_ids.add(journal.journal_id)

    def reverse(
        self,
        journal_id: str,
        original_journal_id: str,
        recorded_at: datetime,
    ) -> JournalEntry:
        """Post a reversal with debit and credit directions inverted.

        Args:
            journal_id: Identifier for the new reversal journal.
            original_journal_id: Identifier of the posted journal to reverse.
            recorded_at: Timezone-aware timestamp for the reversal.

        Returns:
            The immutable reversal journal.
        """
        original = self._journal_for(original_journal_id)
        reversal = JournalEntry(
            journal_id=journal_id,
            recorded_at=recorded_at,
            description=f"Reversal of {original_journal_id}",
            source_event=f"reversal:{original_journal_id}",
            reference=original_journal_id,
            entries=tuple(
                LedgerEntry(
                    account_id=entry.account_id,
                    direction=(
                        EntryDirection.CREDIT
                        if entry.direction is EntryDirection.DEBIT
                        else EntryDirection.DEBIT
                    ),
                    amount=entry.amount,
                    currency=entry.currency,
                )
                for entry in original.entries
            ),
        )
        self.post(reversal)
        return reversal

    def adjust(
        self,
        journal_id: str,
        original_journal_id: str,
        entries: tuple[LedgerEntry, ...],
        recorded_at: datetime,
        description: str,
    ) -> JournalEntry:
        """Post an explicit adjustment linked to an original journal.

        Args:
            journal_id: Identifier for the new adjustment journal.
            original_journal_id: Identifier of the journal being adjusted.
            entries: Balanced Decimal entries for the adjustment.
            recorded_at: Timezone-aware timestamp for the adjustment.
            description: Human-readable correction description.

        Returns:
            The immutable adjustment journal.
        """
        self._journal_for(original_journal_id)
        adjustment = JournalEntry(
            journal_id=journal_id,
            recorded_at=recorded_at,
            description=description,
            source_event=f"adjustment:{original_journal_id}",
            reference=original_journal_id,
            entries=entries,
        )
        self.post(adjustment)
        return adjustment

    def _journal_for(self, journal_id: str) -> JournalEntry:
        try:
            return next(
                journal
                for journal in self._journals
                if journal.journal_id == journal_id
            )
        except StopIteration as exc:
            raise KeyError(f"Journal {journal_id!r} was not found.") from exc

    def balance_for(self, account_id: str, currency: str) -> Decimal:
        """Derive an account balance from posted entries in one currency."""
        expected_currency = CurrencyCode(currency)
        return sum(
            (
                entry.amount
                if entry.direction is EntryDirection.DEBIT
                else -entry.amount
                for journal in self._journals
                for entry in journal.entries
                if entry.account_id == account_id
                and entry.currency == expected_currency
            ),
            Decimal("0"),
        )


__all__ = [
    "EntryDirection",
    "InMemoryLedgerRepository",
    "JournalEntry",
    "LedgerAccountId",
    "LedgerEntry",
    "LedgerRepository",
]

LedgerRepository = InMemoryLedgerRepository
