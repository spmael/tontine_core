import pytest

from tontine.accounts import AccountStatus, AccountType, FinancialAccount
from tontine.exceptions import InvalidCountryError, UnsafeAccountReferenceError


def test_registers_masked_bank_account_with_explicit_currency() -> None:
    account = FinancialAccount(
        account_id="account-1",
        display_name="Community bank account",
        account_type=AccountType.BANK,
        institution_name="Example Bank",
        country="ng",
        currency="NGN",
        masked_reference="****1234",
        custodian_description="Community treasurer custody",
    )

    assert account.account_type is AccountType.BANK
    assert account.currency == "NGN"
    assert account.country == "NG"
    assert account.masked_reference == "****1234"
    assert account.status is AccountStatus.ACTIVE


def test_supports_cash_mobile_wallet_broker_and_other_types() -> None:
    for account_type in AccountType:
        account = FinancialAccount(
            account_id=f"account-{account_type.value}",
            display_name=f"{account_type.value} account",
            account_type=account_type,
            currency="USD",
            masked_reference="cash-****1234",
            institution_name=(
                "Example Institution"
                if account_type
                in {
                    AccountType.BANK,
                    AccountType.MICROFINANCE,
                    AccountType.MOBILE_WALLET,
                    AccountType.BROKER,
                }
                else None
            ),
            country=(
                "US"
                if account_type
                in {
                    AccountType.BANK,
                    AccountType.MICROFINANCE,
                    AccountType.MOBILE_WALLET,
                    AccountType.BROKER,
                }
                else None
            ),
        )

        assert account.account_type is account_type


def test_rejects_unmasked_references_and_credentials() -> None:
    with pytest.raises(UnsafeAccountReferenceError):
        FinancialAccount(
            account_id="account-1",
            display_name="Unsafe account",
            account_type="bank",
            institution_name="Example Bank",
            country="US",
            currency="USD",
            masked_reference="1234567890123456",
        )

    with pytest.raises(UnsafeAccountReferenceError):
        FinancialAccount(
            account_id="account-2",
            display_name="Credential account",
            account_type="bank",
            institution_name="Example Bank",
            country="US",
            currency="USD",
            masked_reference="password=secret",
        )


def test_non_cash_accounts_require_institution_metadata() -> None:
    with pytest.raises(ValueError, match="institution"):
        FinancialAccount(
            account_id="account-1",
            display_name="Missing institution",
            account_type="broker",
            currency="USD",
            masked_reference="****1234",
        )


def test_non_cash_accounts_reject_unknown_iso_country_codes() -> None:
    with pytest.raises(InvalidCountryError, match="ISO 3166-1"):
        FinancialAccount(
            account_id="account-1",
            display_name="Unknown country",
            account_type="bank",
            institution_name="Example Bank",
            country="ZZ",
            currency="USD",
            masked_reference="****1234",
        )


def test_rejects_missing_account_identity_and_reference() -> None:
    with pytest.raises(ValueError, match="identifier"):
        FinancialAccount(
            account_id=" ",
            display_name="Cash account",
            account_type="cash",
            currency="USD",
            masked_reference="****1234",
        )

    with pytest.raises(ValueError, match="display name"):
        FinancialAccount(
            account_id="account-1",
            display_name=" ",
            account_type="cash",
            currency="USD",
            masked_reference="****1234",
        )

    with pytest.raises(UnsafeAccountReferenceError, match="required"):
        FinancialAccount(
            account_id="account-2",
            display_name="Cash account",
            account_type="cash",
            currency="USD",
            masked_reference=" ",
        )

    with pytest.raises(UnsafeAccountReferenceError, match="mask marker"):
        FinancialAccount(
            account_id="account-3",
            display_name="Cash account",
            account_type="cash",
            currency="USD",
            masked_reference="account-reference",
        )


def test_institutional_accounts_require_country() -> None:
    with pytest.raises(ValueError, match="country"):
        FinancialAccount(
            account_id="account-4",
            display_name="Broker account",
            account_type="broker",
            institution_name="Example Broker",
            currency="USD",
            masked_reference="****1234",
        )
