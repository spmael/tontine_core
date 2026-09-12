from datetime import UTC, datetime
from decimal import Decimal

import pytest

from tontine.currencies import CurrencyCode
from tontine.ledger import EntryDirection, JournalEntry, LedgerAccountId, LedgerEntry


@pytest.mark.parametrize(
    ("currency", "amount"),
    [
        ("JPY", Decimal("150000")),
        ("XAF", Decimal("150000")),
        ("EUR", Decimal("150000.25")),
    ],
)
def test_ledger_entry_uses_decimal_amount_and_explicit_currency(
    currency: str,
    amount: Decimal,
) -> None:
    entry = LedgerEntry(
        account_id=f"cash-{currency.lower()}",
        direction=EntryDirection.DEBIT,
        amount=amount,
        currency=currency,
    )

    assert entry.account_id == f"cash-{currency.lower()}"
    assert entry.direction is EntryDirection.DEBIT
    assert entry.amount == amount
    assert entry.currency == CurrencyCode(currency)


def test_ledger_entry_rejects_float_and_negative_amounts() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        LedgerEntry(
            account_id="cash-jpy",
            direction="debit",
            amount=150000.0,
            currency="JPY",
        )

    with pytest.raises(ValueError, match="non-negative"):
        LedgerEntry(
            account_id="cash-eur",
            direction="debit",
            amount=Decimal("-1"),
            currency="EUR",
        )


def test_journal_entry_requires_timezone_aware_provenance() -> None:
    journal = JournalEntry(
        journal_id="journal-001",
        recorded_at=datetime(2027, 1, 15, 12, 0, tzinfo=UTC),
        description="January contribution",
        source_event="contribution-001",
        entries=(
            LedgerEntry("cash-xaf", "debit", Decimal("150000"), "XAF"),
            LedgerEntry("member-capital", "credit", Decimal("150000"), "XAF"),
        ),
        reference="contribution-001",
        actor="treasurer-001",
    )

    assert journal.journal_id == "journal-001"
    assert journal.recorded_at.tzinfo is UTC
    assert journal.entries[0].currency == "XAF"

    with pytest.raises(ValueError, match="timezone-aware"):
        JournalEntry(
            journal_id="journal-002",
            recorded_at=datetime(2027, 1, 15, 12, 0),
            description="Missing timezone",
            source_event="contribution-002",
            entries=(),
        )


def test_ledger_account_id_rejects_empty_and_whitespace_values() -> None:
    assert LedgerAccountId("cash-jpy") == "cash-jpy"

    with pytest.raises(ValueError):
        LedgerAccountId("cash jpy")
