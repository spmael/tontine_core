from decimal import Decimal

import pytest

from tontine.classic import UnpaidContributionPolicy, can_pay_out


def test_unpaid_policy_explicitly_allows_or_denies_payout() -> None:
    assert can_pay_out(Decimal("0"), UnpaidContributionPolicy.ALLOW) is True
    assert can_pay_out(Decimal("1"), UnpaidContributionPolicy.ALLOW) is True
    assert can_pay_out(Decimal("0"), UnpaidContributionPolicy.DENY) is True
    assert can_pay_out(Decimal("1"), UnpaidContributionPolicy.DENY) is False


def test_unpaid_policy_is_required_for_outstanding_contributions() -> None:
    with pytest.raises(ValueError, match="policy"):
        can_pay_out(Decimal("1"), None)
