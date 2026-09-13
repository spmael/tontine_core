from datetime import UTC, datetime
from decimal import Decimal

import pytest

from tontine.ledger import (
    EntryDirection,
    JournalEntry,
    LedgerEntry,
    LedgerRepository,
)


def journal(
    journal_id: str = "journal-001",
    debit: Decimal = Decimal("150000"),
    credit: Decimal = Decimal("150000"),
) -> JournalEntry:
    return JournalEntry(
        journal_id=journal_id,
        recorded_at=datetime(2027, 1, 15, 12, 0, tzinfo=UTC),
        description="January contribution",
        source_event="contribution-001",
        entries=(
            LedgerEntry("cash-xaf", EntryDirection.DEBIT, debit, "XAF"),
            LedgerEntry("member-capital", EntryDirection.CREDIT, credit, "XAF"),
        ),
    )


def test_repository_posts_balanced_journal_and_derives_balances() -> None:
    repository = LedgerRepository()

    repository.post(journal())

    assert repository.balance_for("cash-xaf", "XAF") == Decimal("150000")
    assert repository.balance_for("member-capital", "XAF") == Decimal("-150000")


def test_repository_rejects_unbalanced_journal() -> None:
    with pytest.raises(ValueError, match="balance"):
        LedgerRepository().post(journal(credit=Decimal("149999")))


def test_repository_rejects_journal_without_both_directions() -> None:
    only_debit = JournalEntry(
        journal_id="journal-debit-only",
        recorded_at=datetime(2027, 1, 15, 12, 0, tzinfo=UTC),
        description="Debit only",
        source_event="event-001",
        entries=(LedgerEntry("cash-xaf", "debit", Decimal("1"), "XAF"),),
    )

    with pytest.raises(ValueError, match="debit and credit"):
        LedgerRepository().post(only_debit)

    only_credit = JournalEntry(
        journal_id="journal-credit-only",
        recorded_at=datetime(2027, 1, 15, 12, 0, tzinfo=UTC),
        description="Credit only",
        source_event="event-002",
        entries=(LedgerEntry("cash-xaf", "credit", Decimal("1"), "XAF"),),
    )
    with pytest.raises(ValueError, match="debit and credit"):
        LedgerRepository().post(only_credit)


def test_repository_rejects_mixed_currency_entries() -> None:
    mixed = JournalEntry(
        journal_id="journal-mixed",
        recorded_at=datetime(2027, 1, 15, 12, 0, tzinfo=UTC),
        description="Mixed currencies",
        source_event="event-003",
        entries=(
            LedgerEntry("cash-xaf", "debit", Decimal("1"), "XAF"),
            LedgerEntry("member-capital", "credit", Decimal("1"), "USD"),
        ),
    )

    with pytest.raises(ValueError, match="one currency"):
        LedgerRepository().post(mixed)


def test_ledger_entries_and_journals_validate_values() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        LedgerEntry("cash-xaf", "debit", 1, "XAF")
    with pytest.raises(ValueError, match="non-negative"):
        LedgerEntry("cash-xaf", "debit", Decimal("-1"), "XAF")
    with pytest.raises(ValueError, match="identifier"):
        LedgerEntry(" ", "debit", Decimal("1"), "XAF")
    with pytest.raises(ValueError, match="identifier"):
        LedgerEntry("", "debit", Decimal("1"), "XAF")

    with pytest.raises(ValueError, match="description"):
        JournalEntry(
            "journal-invalid",
            datetime(2027, 1, 15, tzinfo=UTC),
            " ",
            "event",
            (),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        JournalEntry(
            "journal-invalid", datetime(2027, 1, 15), "Description", "event", ()
        )
