from datetime import UTC, datetime
from decimal import Decimal

import pytest

from tontine.exceptions import DuplicateJournalError
from tontine.ledger import EntryDirection, JournalEntry, LedgerEntry, LedgerRepository


def journal(
    journal_id: str = "journal-001",
    amount: Decimal = Decimal("150000"),
) -> JournalEntry:
    return JournalEntry(
        journal_id=journal_id,
        recorded_at=datetime(2027, 1, 15, 12, 0, tzinfo=UTC),
        description="January contribution",
        source_event="contribution-001",
        entries=(
            LedgerEntry("cash-xaf", EntryDirection.DEBIT, amount, "XAF"),
            LedgerEntry("member-capital", EntryDirection.CREDIT, amount, "XAF"),
        ),
    )


def test_posted_journal_and_entries_are_immutable() -> None:
    repository = LedgerRepository()
    posted = journal()
    repository.post(posted)

    with pytest.raises(AttributeError):
        posted.description = "Changed"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        posted.entries[0].amount = Decimal("1")  # type: ignore[misc]


def test_duplicate_journal_ids_are_rejected() -> None:
    repository = LedgerRepository()
    repository.post(journal())

    with pytest.raises(DuplicateJournalError):
        repository.post(journal())


def test_reversal_preserves_original_provenance() -> None:
    repository = LedgerRepository()
    original = journal()
    repository.post(original)

    reversal = repository.reverse(
        journal_id="journal-001-reversal",
        original_journal_id="journal-001",
        recorded_at=datetime(2027, 1, 20, 12, 0, tzinfo=UTC),
    )

    assert reversal.source_event == "reversal:journal-001"
    assert reversal.reference == "journal-001"
    assert repository.balance_for("cash-xaf", "XAF") == Decimal("0")
    assert repository.balance_for("member-capital", "XAF") == Decimal("0")


def test_adjustment_is_explicit_and_traceable() -> None:
    repository = LedgerRepository()
    repository.post(journal())

    adjustment = repository.adjust(
        journal_id="journal-001-adjustment",
        original_journal_id="journal-001",
        entries=(
            LedgerEntry("cash-xaf", "debit", Decimal("100"), "XAF"),
            LedgerEntry("member-capital", "credit", Decimal("100"), "XAF"),
        ),
        recorded_at=datetime(2027, 1, 20, 12, 0, tzinfo=UTC),
        description="Correction",
    )

    assert adjustment.source_event == "adjustment:journal-001"
    assert adjustment.reference == "journal-001"
    assert repository.balance_for("cash-xaf", "XAF") == Decimal("150100")


def test_reversal_and_adjustment_require_existing_journals() -> None:
    repository = LedgerRepository()
    timestamp = datetime(2027, 1, 20, 12, 0, tzinfo=UTC)

    with pytest.raises(KeyError, match="not found"):
        repository.reverse("reversal", "missing", timestamp)

    with pytest.raises(KeyError, match="not found"):
        repository.adjust("adjustment", "missing", (), timestamp, "Correction")
