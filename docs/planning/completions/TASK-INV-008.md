---
task: TASK-INV-008
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-INV-008

## Outcome

Activity currency is validated against its asset. Cross-currency activity needs
a supplied `FxRate` for exactly that pair in either direction and keeps the
original amount, rate, source, and unquantized asset-currency amount. The
registry provides filtered, deterministically ordered activity queries.

## Acceptance Criteria Evidence

- [x] Same-currency and redundant-rate cases:
  `tests/investments/test_activity_validation.py`.
- [x] Pair matching, direction, and unrounded conversion:
  `test_cross_currency_*` tests and `test_fx_rate_converts_in_both_directions_without_rounding`.
- [x] Conflicting asset definitions: `test_registry_rejects_conflicting_asset_definitions`.
- [x] Queries: `test_activity_queries_filter_inclusively_and_order_deterministically`.

## Validation

```text
uv run pytest
189 passed
uv run ruff check src tests
uv run mypy src
```

## Changed Files

- `src/tontine/investments/activity.py`, `src/tontine/investments/fx.py`
- `tests/investments/test_activity_validation.py`, `tests/investments/test_fx_boundary.py`
- `BRD.md`

## Remaining Gaps

Cross-currency activity without an FX rate is now rejected. The zero-amount
policy remains open (TASK-INV-010).
