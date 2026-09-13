---
task: TASK-INV-003
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-INV-003

## Outcome

Implemented Decimal NAV, unit-price, member-value, and ownership calculations
from caller-supplied asset totals, with currency-matched liability aggregation
through `InvestmentValuation.from_liabilities()`.

## Acceptance Criteria Evidence

- [x] Valuations accept caller-supplied asset totals using Decimal-compatible inputs.
- [x] `LiabilityRegistry` aggregates liabilities by currency for valuation construction.
- [x] `InvestmentValuation` derives `NAV = assets - liabilities`.
- [x] Member unit price, attributable value, and ownership percentage derive from supplied units and outstanding totals.
- [x] Focused tests cover valid totals, invalid inputs, cross-currency rejection, and liability validation.

## Validation

```text
uv run pytest tests/investments/test_valuation.py
```

Result: 4 tests passed.

## Files Changed

- `src/tontine/investments/__init__.py`
- `tests/investments/test_valuation.py`
- `docs/planning/tasks/TASK-INV-003.md`

## Gaps and Follow-up

Asset aggregation remains the caller's responsibility in the current baseline.
