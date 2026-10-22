---
task: TASK-INV-007
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-INV-007

## Outcome

`InvestmentValuation` accepts zero units outstanding, exposes
`has_units_outstanding`, and returns `None` for per-unit values in that state.
The investments package is split by capability with public imports preserved.

## Acceptance Criteria Evidence

- [x] Module split with unchanged public imports: `src/tontine/investments/` and
  the existing investment and reporting suites.
- [x] No-units state: `test_valuation_without_units_keeps_nav_and_omits_per_unit_values`
  in `tests/investments/test_valuation.py`.
- [x] Reporting zero values: `test_investment_summary_reports_zero_before_units_are_issued`
  in `tests/reporting/test_member_statement.py`.

## Validation

```text
uv run pytest
189 passed
uv run ruff check src tests
uv run mypy src
```

## Changed Files

- `src/tontine/investments/` (`__init__.py`, `_values.py`, `allocation.py`,
  `assets.py`, `activity.py`, `fx.py`, `valuation.py`)
- `src/tontine/reporting/__init__.py`
- `tests/investments/test_valuation.py`, `tests/reporting/test_member_statement.py`
- `BRD.md`, `README.md`

## Remaining Gaps

`unit_price`, `member_value`, and `member_ownership_percentage` now return
optional values, a pre-1.0 breaking change accepted in ADR-005.
