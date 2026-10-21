from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from tontine.exceptions import InvalidCurrencyError
from tontine.hybrid import split_contribution


@given(
    currency=st.sampled_from(("XAF", "EUR")),
    minor_units=st.integers(min_value=1, max_value=10**9),
    fund_share_bps=st.integers(min_value=0, max_value=10_000),
)
def test_split_always_reconciles_to_amount_received(
    currency: str, minor_units: int, fund_share_bps: int
) -> None:
    unit = Decimal("1") if currency == "XAF" else Decimal("0.01")
    received = unit * minor_units

    pot, fund = split_contribution(received, currency, fund_share_bps)

    assert pot + fund == received


@pytest.mark.parametrize(
    ("received", "currency", "bps", "expected_pot", "expected_fund"),
    [
        ("12345", "XAF", 3000, "8642", "3703"),
        ("12.35", "EUR", 3333, "8.24", "4.11"),
    ],
)
def test_split_rounds_fund_down_and_assigns_remainder_to_pot(
    received: str,
    currency: str,
    bps: int,
    expected_pot: str,
    expected_fund: str,
) -> None:
    assert split_contribution(received, currency, bps) == (
        Decimal(expected_pot),
        Decimal(expected_fund),
    )


@pytest.mark.parametrize(
    ("received", "currency", "bps", "expected"),
    [
        ("1", "XAF", 0, (Decimal("1"), Decimal("0"))),
        ("1", "XAF", 10_000, (Decimal("0"), Decimal("1"))),
        ("0.01", "EUR", 10_000, (Decimal("0.00"), Decimal("0.01"))),
        ("0.01", "EUR", 0, (Decimal("0.01"), Decimal("0.00"))),
    ],
)
def test_split_handles_basis_point_boundaries_and_smallest_units(
    received: str, currency: str, bps: int, expected: tuple[Decimal, Decimal]
) -> None:
    assert split_contribution(received, currency, bps) == expected


@pytest.mark.parametrize("received", ["-1", "-0.01"])
def test_split_rejects_negative_amounts(received: str) -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        split_contribution(received, "EUR", 3000)


@pytest.mark.parametrize("received", ["NaN", "sNaN", "Infinity", "-Infinity"])
def test_split_rejects_non_finite_amounts(received: str) -> None:
    with pytest.raises(ValueError, match="must be finite"):
        split_contribution(received, "EUR", 3000)


@pytest.mark.parametrize(
    ("received", "currency"), [("0", "XAF"), ("0.001", "XAF"), ("0.009", "EUR")]
)
def test_split_rejects_amounts_below_smallest_currency_unit(
    received: str, currency: str
) -> None:
    with pytest.raises(ValueError, match="below the smallest"):
        split_contribution(received, currency, 3000)


@pytest.mark.parametrize("bps", [-1, 10_001, True, 1.0, Decimal("1"), "100"])
def test_split_rejects_invalid_basis_points(bps: object) -> None:
    with pytest.raises((TypeError, ValueError), match="basis points"):
        split_contribution("10", "XAF", bps)  # type: ignore[arg-type]


@pytest.mark.parametrize("received", [True, 1.0, object()])
def test_split_rejects_unsupported_amount_types(received: object) -> None:
    with pytest.raises(TypeError, match="Decimal-compatible"):
        split_contribution(received, "XAF", 3000)  # type: ignore[arg-type]


def test_split_rejects_currency_without_minor_unit() -> None:
    with pytest.raises(ValueError, match="ISO minor unit"):
        split_contribution("1", "XAU", 3000)


def test_split_rejects_unknown_currency() -> None:
    with pytest.raises(InvalidCurrencyError):
        split_contribution("1", "ZZZ", 3000)
