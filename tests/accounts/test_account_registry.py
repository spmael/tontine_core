from datetime import date

import pytest

from tontine.accounts import (
    AccountEventReference,
    AccountEventType,
    AccountStatus,
    FinancialAccount,
    FinancialAccountRegistry,
)
from tontine.exceptions import DuplicateAccountError


def make_account(status: AccountStatus = AccountStatus.ACTIVE) -> FinancialAccount:
    return FinancialAccount(
        account_id="account-1",
        display_name="Community bank account",
        account_type="bank",
        institution_name="Example Bank",
        country="NG",
        currency="NGN",
        masked_reference="****1234",
        status=status,
    )


def test_registry_registers_and_retrieves_account() -> None:
    registry = FinancialAccountRegistry()
    account = make_account()

    registry.register(account)

    assert registry.get("account-1") is account


def test_registry_rejects_duplicate_account_ids() -> None:
    registry = FinancialAccountRegistry()
    registry.register(make_account())

    with pytest.raises(DuplicateAccountError):
        registry.register(make_account())


def test_event_reference_requires_active_registered_account() -> None:
    registry = FinancialAccountRegistry()
    registry.register(make_account())

    reference = registry.record_event(
        event_id="contribution-1",
        event_type=AccountEventType.CONTRIBUTION,
        account_id="account-1",
        event_date=date(2027, 1, 15),
    )

    assert reference == AccountEventReference(
        event_id="contribution-1",
        event_type=AccountEventType.CONTRIBUTION,
        account_id="account-1",
        event_date=date(2027, 1, 15),
    )
    assert registry.events_for("account-1") == (reference,)


def test_registry_links_account_to_logical_ledger_identifier() -> None:
    registry = FinancialAccountRegistry()
    registry.register(make_account())

    registry.link_ledger_account("account-1", "ledger-cash-ngn")

    assert registry.ledger_account_for("account-1") == "ledger-cash-ngn"


def test_registry_rejects_missing_and_inactive_account_references() -> None:
    registry = FinancialAccountRegistry()

    with pytest.raises(KeyError):
        registry.record_event(
            event_id="payout-1",
            event_type="payout",
            account_id="missing",
            event_date=date(2027, 1, 15),
        )

    registry.register(make_account(AccountStatus.INACTIVE))
    with pytest.raises(ValueError, match="inactive"):
        registry.record_event(
            event_id="payout-1",
            event_type="payout",
            account_id="account-1",
            event_date=date(2027, 1, 15),
        )


def test_registry_rejects_invalid_ledger_links_and_missing_ledger_links() -> None:
    registry = FinancialAccountRegistry()
    registry.register(make_account())

    with pytest.raises(ValueError, match="invalid"):
        registry.link_ledger_account("account-1", "ledger account")

    with pytest.raises(KeyError, match="linked"):
        registry.ledger_account_for("account-1")

    with pytest.raises(KeyError, match="not found"):
        registry.get("missing")
