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
