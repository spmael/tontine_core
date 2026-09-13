from datetime import UTC, date, datetime
from decimal import Decimal

import tontine
from tontine.classic import ClassicRotation
from tontine.investments import AllocationRule
from tontine.ledger import EntryDirection, JournalEntry, LedgerEntry
from tontine.reporting import InvestmentSummary, build_member_statement


def test_public_api_creates_group_and_cycle_without_infrastructure() -> None:
    group = tontine.create_group("group-1", "Community Circle", "JPY", "CM")
    cycle = tontine.create_contribution_cycle(
        "2027-01", date(2027, 1, 1), date(2027, 1, 31), "Asia/Tokyo"
    )

    assert group.base_currency == "JPY"
    assert group.jurisdiction == "CM"
    assert cycle.cycle_id == "2027-01"


def test_public_api_keeps_classic_investment_ledger_and_reporting_boundaries() -> None:
    rotation = ClassicRotation.from_active_members(("member-a", "member-b"))
    allocation = AllocationRule({"cash": Decimal("100")})
    journal = JournalEntry(
        journal_id="journal-1",
        recorded_at=datetime(2027, 1, 1, tzinfo=UTC),
        description="Contribution",
        source_event="contribution-1",
        entries=(
            LedgerEntry("cash", EntryDirection.DEBIT, Decimal("100"), "JPY"),
            LedgerEntry("capital", EntryDirection.CREDIT, Decimal("100"), "JPY"),
        ),
    )
    statement = build_member_statement(
        "member-a",
        "Member A",
        "JPY",
        (),
        (),
        InvestmentSummary(Decimal("0"), Decimal("0"), Decimal("0"), "JPY"),
    )

    assert rotation.recipient_for_cycle(1) == "member-a"
    assert allocation.total_percentage == Decimal("100")
    assert journal.source_event == "contribution-1"
    assert statement.base_currency == "JPY"