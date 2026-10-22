from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from tontine.classic import ClassicRotation
from tontine.exceptions import MissingRecordError
from tontine.governance import (
    GovernanceRegistry,
    GovernanceSnapshot,
    InvestmentAuthorizationEffect,
    ProposalStatus,
    VoteChoice,
)
from tontine.investments import (
    AssetCategory,
    AssetDefinition,
    DecisionReference,
    FxRate,
    InvestmentActivityRegistry,
    InvestmentActivityType,
)

MEMBERS = ("member-a", "member-b", "member-c")
CREATED_AT = datetime(2027, 1, 1, tzinfo=UTC)
OPENED_AT = datetime(2027, 1, 2, tzinfo=UTC)
VOTED_AT = datetime(2027, 1, 3, tzinfo=UTC)
DEADLINE = datetime(2027, 1, 10, tzinfo=UTC)
TESLA = AssetDefinition("tsla", "Tesla", AssetCategory.EQUITY, "USD")


def authorization(
    activity_type: str = "purchase", max_amount: str = "1000"
) -> InvestmentAuthorizationEffect:
    return InvestmentAuthorizationEffect(
        asset_id="tsla",
        activity_type=InvestmentActivityType(activity_type),
        max_amount=Decimal(max_amount),
        currency="USD",
    )


def governance_with(
    proposal_id: str = "buy-tesla",
    effect: InvestmentAuthorizationEffect | None = None,
    *,
    approve: bool = True,
) -> GovernanceRegistry:
    governance = GovernanceRegistry(
        MEMBERS, ClassicRotation.from_active_members(MEMBERS)
    )
    governance.create_investment_authorization_proposal(
        proposal_id=proposal_id,
        title="Buy Tesla",
        description="Authorize Tesla purchases up to USD 1000.",
        proposer_id="member-a",
        authorization=effect or authorization(),
        effective_cycle=2,
        current_cycle=1,
        approval_threshold=Decimal("60"),
        created_at=CREATED_AT,
        voting_deadline=DEADLINE,
    )
    governance.open_proposal(proposal_id, occurred_at=OPENED_AT)
    choice = VoteChoice.YES if approve else VoteChoice.NO
    for member_id in MEMBERS:
        governance.vote(proposal_id, member_id, choice, occurred_at=VOTED_AT)
    governance.evaluate(proposal_id, occurred_at=DEADLINE)
    return governance


def purchase(
    registry: InvestmentActivityRegistry,
    event_id: str,
    amount: str,
    *,
    event_type: str = "purchase",
    currency: str = "USD",
    proposal_id: str = "buy-tesla",
    fx_rate: FxRate | None = None,
) -> None:
    registry.record_activity(
        event_id=event_id,
        event_type=InvestmentActivityType(event_type),
        asset=TESLA,
        amount=Decimal(amount),
        currency=currency,
        effective_date=date(2027, 2, 1),
        recorded_at=VOTED_AT,
        source="broker_statement",
        fx_rate=fx_rate,
        authorization=DecisionReference(proposal_id),
        units=Decimal("1") if event_type in {"purchase", "sale"} else None,
    )


def test_effect_accepts_only_positive_purchase_or_sale_limits() -> None:
    effect = authorization("sale", "1")
    assert effect.activity_type is InvestmentActivityType.SALE
    assert effect.currency == "USD"

    with pytest.raises(ValueError, match="purchases or sales"):
        authorization("fee")
    with pytest.raises(ValueError, match="positive"):
        authorization(max_amount="0")
    with pytest.raises(ValueError, match="asset"):
        InvestmentAuthorizationEffect(
            " ", InvestmentActivityType.PURCHASE, Decimal("1"), "USD"
        )


def test_approved_authorization_is_audited_and_survives_snapshot() -> None:
    governance = governance_with()

    effect = governance.approved_investment_authorization("buy-tesla")
    assert effect == authorization()
    assert any(
        event.event_type == "investment_authorization_approved"
        and event.details["max_amount"] == "1000"
        for event in governance.audit_events("buy-tesla")
    )
    restored = GovernanceRegistry.from_snapshot(governance.snapshot())
    assert restored.approved_investment_authorization("buy-tesla") == effect
    assert isinstance(restored.snapshot(), GovernanceSnapshot)


def test_lookup_rejects_unknown_unapproved_or_non_investment_proposals() -> None:
    rejected = governance_with(approve=False)
    with pytest.raises(ValueError, match="not approved"):
        rejected.approved_investment_authorization("buy-tesla")
    with pytest.raises(MissingRecordError):
        rejected.approved_investment_authorization("missing")

    governance = GovernanceRegistry(
        MEMBERS, ClassicRotation.from_active_members(MEMBERS)
    )
    governance.create_rotation_exception_proposal(
        proposal_id="exception",
        title="Swap",
        description="Swap recipient.",
        proposer_id="member-a",
        exception_id="exception-1",
        recipient_id="member-c",
        cycle_number=2,
        current_cycle=1,
        approval_threshold=Decimal("60"),
        created_at=CREATED_AT,
        voting_deadline=DEADLINE,
    )
    governance.open_proposal("exception", occurred_at=OPENED_AT)
    for member_id in MEMBERS:
        governance.vote("exception", member_id, VoteChoice.YES, occurred_at=VOTED_AT)
    assert (
        governance.evaluate("exception", occurred_at=DEADLINE)
        is ProposalStatus.APPROVED
    )
    with pytest.raises(ValueError, match="does not authorize"):
        governance.approved_investment_authorization("exception")


def test_authorized_purchases_are_limited_cumulatively() -> None:
    registry = InvestmentActivityRegistry(governance_with())

    purchase(registry, "fill-1", "600")
    purchase(registry, "fill-2", "400")
    with pytest.raises(ValueError, match="exceeds the maximum"):
        purchase(registry, "fill-3", "0.01")

    assert registry.authorized_total("buy-tesla") == Decimal("1000")
    assert registry.activities()[0].authorization == DecisionReference("buy-tesla")


def test_cross_currency_authorized_activity_counts_asset_currency_amount() -> None:
    registry = InvestmentActivityRegistry(governance_with())
    usd_jpy = FxRate("USD", "JPY", Decimal("150"), VOTED_AT, "broker")

    purchase(registry, "fill-1", "150000", currency="JPY", fx_rate=usd_jpy)

    assert registry.authorized_total("buy-tesla") == Decimal("1000")


def test_authorization_must_match_activity_and_requires_lookup() -> None:
    registry = InvestmentActivityRegistry(governance_with())

    with pytest.raises(ValueError, match="does not authorize this activity"):
        purchase(registry, "sale-1", "1", event_type="sale")
    with pytest.raises(ValueError, match="Only purchases and sales"):
        purchase(registry, "fee-1", "1", event_type="fee")
    with pytest.raises(MissingRecordError):
        purchase(registry, "buy-1", "1", proposal_id="missing")
    with pytest.raises(ValueError, match="require an authorization lookup"):
        purchase(InvestmentActivityRegistry(), "buy-2", "1")
    with pytest.raises(ValueError, match="identifier is required"):
        DecisionReference(" ")
    assert registry.activities() == ()


def test_unapproved_authorization_is_rejected_for_activity() -> None:
    registry = InvestmentActivityRegistry(governance_with(approve=False))

    with pytest.raises(ValueError, match="not approved"):
        purchase(registry, "buy-1", "1")
