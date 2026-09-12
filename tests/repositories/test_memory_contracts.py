from typing import Protocol

import pytest

from tontine.accounts import FinancialAccount
from tontine.groups import Group
from tontine.repositories import (
    AccountRepository,
    GroupRepository,
    InMemoryAccountRepository,
    InMemoryGroupRepository,
)


def make_group(group_id: str) -> Group:
    return Group.create_draft(group_id, f"Group {group_id}", "JPY")


def make_account(account_id: str) -> FinancialAccount:
    return FinancialAccount(
        account_id=account_id,
        display_name="Cash account",
        account_type="cash",
        currency="JPY",
        masked_reference="****1234",
    )


def test_group_repository_has_deterministic_listing_and_duplicate_rules() -> None:
    repository: GroupRepository = InMemoryGroupRepository()
    repository.add(make_group("group-b"))
    repository.add(make_group("group-a"))

    assert repository.get("group-a").group_id == "group-a"
    assert [group.group_id for group in repository.list()] == ["group-a", "group-b"]
    with pytest.raises(ValueError, match="already"):
        repository.add(make_group("group-a"))
    with pytest.raises(KeyError):
        repository.get("missing")


def test_account_repository_has_deterministic_listing_and_protocol_shape() -> None:
    repository: AccountRepository = InMemoryAccountRepository()
    repository.add(make_account("account-b"))
    repository.add(make_account("account-a"))

    assert repository.get("account-a").account_id == "account-a"
    assert [account.account_id for account in repository.list()] == [
        "account-a",
        "account-b",
    ]
    assert isinstance(repository, Protocol) is False
