from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

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


def test_balance_for_includes_journals_at_inclusive_as_of_boundary() -> None:
    repository = LedgerRepository()
    posted = journal()
    repository.post(posted)

    assert repository.balance_for(
        "cash-xaf",
        "XAF",
        as_of=datetime(2027, 1, 15, 11, 59, tzinfo=UTC),
    ) == Decimal("0")
    assert repository.balance_for(
        "cash-xaf",
        "XAF",
        as_of=posted.recorded_at,
    ) == Decimal("150000")
    assert repository.balance_for(
        "cash-xaf",
        "XAF",
        as_of=datetime(2027, 1, 15, 13, tzinfo=timezone(timedelta(hours=1))),
    ) == Decimal("150000")


def test_historical_projection_handles_out_of_order_posts_and_rebuild() -> None:
    repository = LedgerRepository()
    later = replace(
        journal("later", Decimal("100"), Decimal("100")),
        recorded_at=datetime(2027, 1, 20, 12, tzinfo=UTC),
    )
    earlier = replace(
        journal("earlier", Decimal("50"), Decimal("50")),
        recorded_at=datetime(2027, 1, 10, 12, tzinfo=UTC),
    )
    same_time = replace(
        journal("same-time", Decimal("25"), Decimal("25")),
        recorded_at=later.recorded_at,
    )
    repository.post(later)
    repository.post(earlier)
    repository.post(same_time)

    assert repository.balance_for(
        "cash-xaf",
        "XAF",
        as_of=datetime(2027, 1, 15, 12, tzinfo=UTC),
    ) == Decimal("50")
    assert repository.balance_for(
        "cash-xaf",
        "XAF",
        as_of=later.recorded_at,
    ) == Decimal("175")
    assert repository.balance_for("cash-xaf", "XAF") == Decimal("175")

    repository._balances.clear()
    repository._balance_history.clear()
    repository.rebuild_balance_projection()

    assert repository.balance_for(
        "cash-xaf",
        "XAF",
        as_of=datetime(2027, 1, 15, 12, tzinfo=UTC),
    ) == Decimal("50")
    assert repository.balance_for(
        "cash-xaf",
        "XAF",
        as_of=later.recorded_at,
    ) == Decimal("175")


def test_balance_for_rejects_naive_as_of_without_changing_balances() -> None:
    repository = LedgerRepository()
    repository.post(journal())

    with pytest.raises(ValueError, match="as_of must be timezone-aware"):
        repository.balance_for("cash-xaf", "XAF", as_of=datetime(2027, 1, 20))

    assert repository.balance_for("cash-xaf", "XAF") == Decimal("150000")


def test_balance_for_distinguishes_repeated_local_time_by_fold() -> None:
    repository = LedgerRepository()
    local_zone = ZoneInfo("America/New_York")
    recorded_at = datetime(2027, 11, 7, 1, 30, tzinfo=local_zone, fold=1)
    repository.post(replace(journal(), recorded_at=recorded_at))

    assert repository.balance_for(
        "cash-xaf",
        "XAF",
        as_of=datetime(2027, 11, 7, 1, 30, tzinfo=local_zone, fold=0),
    ) == Decimal("0")
    assert repository.balance_for(
        "cash-xaf",
        "XAF",
        as_of=recorded_at,
    ) == Decimal("150000")


def test_projection_tracks_multiple_accounts_and_currencies_and_rebuilds() -> None:
    repository = LedgerRepository()
    repository.post(journal())
    repository.post(
        JournalEntry(
            journal_id="journal-usd",
            recorded_at=datetime(2027, 1, 16, 12, 0, tzinfo=UTC),
            description="USD contribution",
            source_event="contribution-usd",
            entries=(
                LedgerEntry("cash-usd", "debit", Decimal("25"), "USD"),
                LedgerEntry("member-capital-usd", "credit", Decimal("25"), "USD"),
            ),
        )
    )
    repository.reverse(
        "journal-001-reversal",
        "journal-001",
        datetime(2027, 1, 20, 12, 0, tzinfo=UTC),
    )
    repository.adjust(
        "journal-001-adjustment",
        "journal-001",
        (
            LedgerEntry("cash-xaf", "debit", Decimal("100"), "XAF"),
            LedgerEntry("member-capital", "credit", Decimal("100"), "XAF"),
        ),
        datetime(2027, 1, 21, 12, 0, tzinfo=UTC),
        "Correction",
    )

    keys = (
        ("cash-xaf", "XAF"),
        ("member-capital", "XAF"),
        ("cash-usd", "USD"),
        ("member-capital-usd", "USD"),
        ("cash-usd", "XAF"),
    )
    for account_id, currency in keys:
        expected = sum(
            (
                entry.amount
                if entry.direction is EntryDirection.DEBIT
                else -entry.amount
                for posted in repository.journals()
                for entry in posted.entries
                if entry.account_id == account_id and entry.currency == currency
            ),
            Decimal("0"),
        )
        assert repository.balance_for(account_id, currency) == expected

    assert repository.balance_for("cash-xaf", "XAF") == Decimal("100")
    assert repository.balance_for("cash-usd", "USD") == Decimal("25")
    repository._balances.clear()
    repository.rebuild_balance_projection()
    for account_id, currency in keys:
        assert repository.balance_for(account_id, currency) == sum(
            (
                entry.amount
                if entry.direction is EntryDirection.DEBIT
                else -entry.amount
                for posted in repository.journals()
                for entry in posted.entries
                if entry.account_id == account_id and entry.currency == currency
            ),
            Decimal("0"),
        )


def test_invalid_post_does_not_change_journal_history_or_projection() -> None:
    repository = LedgerRepository()
    repository.post(journal())
    posted_journals = repository.journals()
    cash_balance = repository.balance_for("cash-xaf", "XAF")
    assert isinstance(posted_journals, tuple)

    with pytest.raises(ValueError, match="balance"):
        repository.post(journal("unbalanced", credit=Decimal("149999")))

    assert repository.journals() == posted_journals
    assert repository.balance_for("cash-xaf", "XAF") == cash_balance


def test_rebuild_rejects_invalid_history_without_replacing_projection() -> None:
    repository = LedgerRepository()
    repository.post(journal())
    original_balance = repository.balance_for("cash-xaf", "XAF")
    repository._journals.append(journal("invalid", credit=Decimal("149999")))

    with pytest.raises(ValueError, match="balance"):
        repository.rebuild_balance_projection()

    assert repository.balance_for("cash-xaf", "XAF") == original_balance


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
    with pytest.raises(
        ValueError,
        match=(
            r"recorded_at must be timezone-aware.*datetime\.timezone\.utc.*"
            r"zoneinfo\.ZoneInfo"
        ),
    ):
        JournalEntry(
            "journal-invalid", datetime(2027, 1, 15), "Description", "event", ()
        )
