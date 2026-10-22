---
task: TASK-INV-009
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-INV-009

## Outcome

Purchases and sales can carry a `DecisionReference`. The activity registry
validates it through an optional `InvestmentAuthorizationLookup`, requires a
matching asset, type, and currency, and enforces the decision maximum
cumulatively in asset-currency amounts.

## Acceptance Criteria Evidence

- [x] Cumulative limit: `test_authorized_purchases_are_limited_cumulatively`.
- [x] Cross-currency totals: `test_cross_currency_authorized_activity_counts_asset_currency_amount`.
- [x] Mismatch, income/fee, missing lookup, unknown decision:
  `test_authorization_must_match_activity_and_requires_lookup`.
- [x] Unapproved decision: `test_unapproved_authorization_is_rejected_for_activity`.

All in `tests/governance/test_investment_authorization.py`.

## Validation

```text
uv run pytest
189 passed
uv run ruff check src tests
uv run mypy src
```

## Changed Files

- `src/tontine/investments/activity.py`, `src/tontine/investments/__init__.py`
- `tests/governance/test_investment_authorization.py`

## Remaining Gaps

None for this task.
