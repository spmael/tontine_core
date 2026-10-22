from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

import pytest

import tontine.hybrid as hybrid
from tontine.exceptions import InvalidCurrencyError, MissingRecordError
from tontine.hybrid import (
    CatchUpOutcome,
    CatchUpPolicy,
    ContributionPaymentOrder,
    ExitFeeSchedule,
    HybridRule,
    HybridRuleSchedule,
    HybridRuleVersion,
    LegalForm,
    PayoutDeferralPolicy,
    PenaltyPaymentOrder,
    StatuteFlags,
)


def rule() -> HybridRule:
    return HybridRule("XAF", 3000, Decimal("1000"), 30)


def version(number: int = 1, effective: int = 1, adopted: int = 0) -> HybridRuleVersion:
    return HybridRuleVersion(number, effective, adopted, rule())


def test_public_defaults_and_currency_normalization() -> None:
    item = replace(rule(), currency=" xaf ")
    assert item.currency == "XAF"
    assert item.penalty_order is PenaltyPaymentOrder.PENALTY_FIRST
    assert item.contribution_order is ContributionPaymentOrder.POT_FIRST
    assert item.catch_up == CatchUpPolicy(True, 1, CatchUpOutcome.FORFEIT)
    assert item.exit_fees == ExitFeeSchedule()
    assert item.legal_form is LegalForm.UNREGISTERED
    assert item.statute_flags == StatuteFlags(False, False, True)
    assert item.payout_deferral == PayoutDeferralPolicy(True, 12)
    assert item.payout_deferral.HARD_MAX_MONTHS == 24
    assert version().governance_decision_ref is None
    for name in hybrid.__all__:
        assert getattr(hybrid, name).__doc__


@pytest.mark.parametrize("share", [0, 1, 9999, 10_000])
def test_fund_share_accepts_inclusive_boundaries(share: int) -> None:
    assert replace(rule(), fund_share_bps=share).fund_share_bps == share


@pytest.mark.parametrize("share", [-1, 10_001, True, 1.0, Decimal("1"), "100"])
def test_fund_share_rejects_non_integer_and_out_of_range(share: object) -> None:
    with pytest.raises((ValueError, TypeError), match="Fund share"):
        replace(rule(), fund_share_bps=share)


@pytest.mark.parametrize("price", ["0", "-0", "-1", "NaN", "sNaN", "Infinity"])
def test_launch_price_rejects_non_positive_or_nonfinite(price: str) -> None:
    with pytest.raises(ValueError, match="Launch unit price"):
        replace(rule(), launch_unit_price=Decimal(price))


def test_launch_price_is_exact_decimal_not_rounded_to_minor_unit() -> None:
    assert replace(rule(), launch_unit_price=Decimal("0.12345")).launch_unit_price == (
        Decimal("0.12345")
    )
    with pytest.raises(TypeError, match="Decimal"):
        replace(rule(), launch_unit_price=1000)


@pytest.mark.parametrize("currency", ["XAU", "XXX", "XTS"])
def test_currency_requires_iso_minor_unit(currency: str) -> None:
    with pytest.raises(ValueError, match="minor unit"):
        replace(rule(), currency=currency)


def test_unknown_currency_is_rejected() -> None:
    with pytest.raises(InvalidCurrencyError):
        replace(rule(), currency="INVALID")


@pytest.mark.parametrize("penalty", list(PenaltyPaymentOrder))
@pytest.mark.parametrize("contribution", list(ContributionPaymentOrder))
def test_closed_partial_payment_orders(
    penalty: PenaltyPaymentOrder, contribution: ContributionPaymentOrder
) -> None:
    item = replace(rule(), penalty_order=penalty, contribution_order=contribution)
    assert item.penalty_order is penalty
    assert item.contribution_order is contribution


@pytest.mark.parametrize(
    "changes",
    [
        {"penalty_order": "other"},
        {"contribution_order": "fund_first"},
        {"legal_form": "other"},
        {"max_valuation_age_days": -1},
        {"max_valuation_age_days": True},
        {"max_valuation_age_days": 1.5},
        {"catch_up": {}},
        {"exit_fees": {}},
        {"statute_flags": {}},
        {"payout_deferral": {}},
    ],
)
def test_invalid_rule_settings_are_rejected(changes: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        replace(rule(), **changes)


def test_catch_up_choices_and_deadline() -> None:
    assert not CatchUpPolicy(allowed=False).allowed
    assert CatchUpPolicy(deadline_cycles=2).deadline_cycles == 2
    for invalid in (0, -1, True, 1.5):
        with pytest.raises((TypeError, ValueError)):
            CatchUpPolicy(deadline_cycles=invalid)
    with pytest.raises(TypeError):
        CatchUpPolicy(allowed=1)
    with pytest.raises(ValueError):
        CatchUpPolicy(default_outcome="catch_up")


@pytest.mark.parametrize("fee", ["-1", "100", "101", "NaN", "Infinity"])
def test_exit_fee_bounds(fee: str) -> None:
    with pytest.raises(ValueError):
        ExitFeeSchedule(voluntary=Decimal(fee))
    with pytest.raises(ValueError):
        ExitFeeSchedule(expulsion=Decimal(fee))


def test_death_is_free_and_statute_flags_are_explicit() -> None:
    with pytest.raises(ValueError, match="Death"):
        ExitFeeSchedule(death=Decimal("1"))
    with pytest.raises(TypeError, match="Decimal"):
        ExitFeeSchedule(voluntary=0.5)
    with pytest.raises(ValueError, match="one fee schedule"):
        StatuteFlags(uniform_fee_schedule=False)
    for name in (
        "unconditional_redemption_refusal",
        "pro_rata_wind_up",
        "uniform_fee_schedule",
    ):
        with pytest.raises(TypeError, match="boolean"):
            replace(StatuteFlags(), **{name: 1})


def test_cooperative_expulsion_limit_and_other_forms_warning() -> None:
    fees = ExitFeeSchedule(voluntary=Decimal("1"), expulsion=Decimal("2"))
    with pytest.raises(ValueError, match="Expulsion fee"):
        replace(rule(), exit_fees=fees, legal_form=LegalForm.COOPERATIVE)
    for form in (LegalForm.ASSOCIATION, LegalForm.UNREGISTERED):
        with pytest.warns(UserWarning, match="Expulsion fee"):
            assert replace(rule(), exit_fees=fees, legal_form=form).exit_fees == fees
    assert replace(
        rule(),
        exit_fees=ExitFeeSchedule(Decimal("2"), Decimal("2")),
        legal_form=LegalForm.COOPERATIVE,
    ).exit_fees.expulsion == Decimal("2")


def test_default_deferral_cannot_pre_authorize_governance_extension() -> None:
    assert PayoutDeferralPolicy(max_months=1, at_cycle_end=False).max_months == 1
    for invalid in (0, -1, 13, 24, 25, True, 1.5):
        with pytest.raises((ValueError, TypeError)):
            PayoutDeferralPolicy(max_months=invalid)
    with pytest.raises(TypeError):
        PayoutDeferralPolicy(at_cycle_end=1)


def test_effective_resolution_ties_missing_and_immutable_extension() -> None:
    initial = HybridRuleSchedule("group-1", (version(),))
    later = version(2, 4, 2)
    tie = replace(version(3, 4, 2), governance_decision_ref="decision-1")
    extended = initial.with_version(later, current_cycle=2).with_version(
        tie, current_cycle=2
    )
    assert initial.version_for_cycle(10) == version()
    assert extended.version_for_cycle(3) == version()
    assert extended.version_for_cycle(4) == tie
    assert extended.version_for_cycle(99) == tie
    restored = HybridRuleSchedule("group-1", (tie, version(), later))
    assert restored == extended
    with pytest.raises(MissingRecordError, match="cycle 1"):
        HybridRuleSchedule("group-1", (later,)).version_for_cycle(1)
    for invalid in (0, -1, True, 1.5):
        with pytest.raises((ValueError, TypeError)):
            extended.version_for_cycle(invalid)


def test_non_retroactivity_and_future_adoption_are_rejected() -> None:
    schedule = HybridRuleSchedule("group-1", (version(),))
    with pytest.raises(ValueError, match="after the current"):
        schedule.with_version(version(2, 2, 1), current_cycle=2)
    with pytest.raises(ValueError, match="future"):
        schedule.with_version(version(2, 4, 3), current_cycle=2)
    with pytest.raises(ValueError, match="unique"):
        schedule.with_version(version(1, 4, 2), current_cycle=2)
    with pytest.raises(ValueError, match="currency"):
        schedule.with_version(
            replace(version(2, 4, 2), rule=replace(rule(), currency="EUR")),
            current_cycle=2,
        )


def test_fee_change_requires_a_complete_intervening_cycle() -> None:
    schedule = HybridRuleSchedule("group-1", (version(),))
    changed = replace(rule(), exit_fees=ExitFeeSchedule(voluntary=Decimal("1")))
    too_soon = replace(version(2, 3, 2), rule=changed)
    with pytest.raises(ValueError, match="full cycle"):
        schedule.with_version(too_soon, current_cycle=2)
    with pytest.raises(ValueError, match="full cycle"):
        HybridRuleSchedule("group-1", (version(), too_soon))
    valid = replace(too_soon, effective_cycle=4)
    extended = schedule.with_version(valid, current_cycle=2)
    assert extended.version_for_cycle(3).rule.exit_fees == ExitFeeSchedule()
    assert extended.version_for_cycle(4).rule.exit_fees == changed.exit_fees
    assert schedule.with_version(version(2, 3, 2), current_cycle=2)


def test_inserting_before_first_scheduled_rule_cannot_bypass_fee_notice() -> None:
    schedule = HybridRuleSchedule("group-1", (version(1, 5, 0),))
    earlier = replace(
        version(2, 3, 2),
        rule=replace(rule(), exit_fees=ExitFeeSchedule(voluntary=Decimal("1"))),
    )
    with pytest.raises(ValueError, match="full cycle"):
        schedule.with_version(earlier, current_cycle=2)


def test_adding_versions_validates_current_cycle_and_value_type() -> None:
    schedule = HybridRuleSchedule("group-1", (version(),))
    for invalid in (-1, True, 1.5):
        with pytest.raises((TypeError, ValueError)):
            schedule.with_version(version(2, 3, 1), current_cycle=invalid)
    with pytest.raises(TypeError, match="HybridRuleVersion"):
        schedule.with_version(rule(), current_cycle=1)


def test_adding_an_earlier_version_preserves_future_fee_notice() -> None:
    future = version(2, 5, 4)
    schedule = HybridRuleSchedule("group-1", (version(), future))
    earlier = replace(
        version(3, 4, 1),
        rule=replace(rule(), exit_fees=ExitFeeSchedule(voluntary=Decimal("1"))),
    )
    with pytest.raises(ValueError, match="full cycle"):
        schedule.with_version(earlier, current_cycle=2)


@pytest.mark.parametrize(
    "changes",
    [
        {"version": 0},
        {"version": True},
        {"effective_cycle": 0},
        {"adopted_cycle": -1},
        {"adopted_cycle": 1},
        {"governance_decision_ref": " "},
        {"rule": {}},
    ],
)
def test_invalid_version_metadata(changes: dict[str, object]) -> None:
    with pytest.raises((ValueError, TypeError)):
        replace(version(), **changes)


def test_schedule_validation_and_nested_immutability() -> None:
    for group_id in ("", " ", "group 1"):
        with pytest.raises(ValueError, match="identifier"):
            HybridRuleSchedule(group_id, (version(),))
    with pytest.raises(ValueError, match="at least one"):
        HybridRuleSchedule("group-1", ())
    with pytest.raises(TypeError, match="HybridRuleVersion"):
        HybridRuleSchedule("group-1", (rule(),))
    source = [version()]
    schedule = HybridRuleSchedule("group-1", source)
    source.clear()
    assert len(schedule.versions) == 1
    for item, name, value in (
        (schedule, "group_id", "other"),
        (schedule.versions[0], "version", 2),
        (rule(), "fund_share_bps", 0),
        (rule().exit_fees, "voluntary", Decimal("2")),
        (rule().catch_up, "allowed", False),
        (rule().statute_flags, "pro_rata_wind_up", True),
        (rule().payout_deferral, "max_months", 1),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(item, name, value)
