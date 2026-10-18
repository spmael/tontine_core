---
task: TASK-INV-010
status: shipped
started: 2026-10-19
completed: 2026-10-19
---

# Completion: TASK-INV-010

## Outcome

Purchase, sale, income, and fee amounts must be strictly positive and at least
one smallest ISO 4217 unit of both the activity currency and, after conversion,
the asset currency. A per-type `_ZERO_AMOUNT_ALLOWED` table drives the rule, and
`tontine.currencies.smallest_unit` supplies the minor units. Nothing is rounded.
Purchases and sales require strictly positive asset `units` from a per-type
`_UNITS_REQUIRED` table; income and fees reject units.
ADR-005 records the decision and its follow-ups.

## Acceptance Criteria Evidence

- [x] Zero spellings for every type:
  `test_zero_amount_is_rejected_for_every_activity_type`.
- [x] Negative and non-finite amounts:
  `test_negative_amount_is_rejected_for_every_activity_type`,
  `test_non_finite_amount_is_rejected`.
- [x] Per-type table: `test_zero_amount_policy_covers_every_activity_type`.
- [x] Guidance message:
  `test_zero_amount_rejection_points_to_the_supported_alternatives`.
- [x] Sub-unit and minimum amounts:
  `test_amount_below_smallest_currency_unit_is_rejected_not_rounded`,
  `test_smallest_currency_unit_and_finer_precision_above_it_are_accepted`.
- [x] Converted amounts:
  `test_converted_asset_amount_below_smallest_asset_unit_is_rejected`,
  `test_converted_asset_amount_at_or_above_smallest_unit_is_accepted`.
- [x] Direct construction:
  `test_direct_activity_construction_applies_the_same_amount_policy`.
- [x] Minor units: `tests/currencies/test_currency_code.py`.
- [x] Purchase and sale units:
  `test_units_policy_covers_every_activity_type`,
  `test_purchase_and_sale_record_positive_units`,
  `test_non_positive_units_are_rejected_for_purchase_and_sale`,
  `test_non_finite_units_are_rejected`, `test_purchase_and_sale_require_units`,
  `test_income_and_fee_reject_units`,
  `test_non_positive_units_point_to_the_corporate_action_path`,
  `test_direct_activity_construction_applies_the_same_units_policy`.

Activity tests are in `tests/investments/test_activity_validation.py`.

## Validation

```text
uv run pytest
261 passed
uv run ruff check src tests
uv run mypy src
```

## Changed Files

- `src/tontine/investments/activity.py`
- `src/tontine/currencies/__init__.py`
- `tests/investments/test_activity.py`, `tests/investments/test_activity_validation.py`
- `tests/governance/test_investment_authorization.py`
- `tests/currencies/test_currency_code.py`
- `docs/architecture/adr/ADR-005-investment-activity-and-valuation-policy.md`
- `BRD.md`, CAP-INV-002, TASK-INV-010

## Remaining Gaps

Reversal entries, typed waiver and cancellation events, and the corporate-action
type are follow-ups recorded in ADR-005, not built here.
