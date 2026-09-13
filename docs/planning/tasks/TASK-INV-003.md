---
id: TASK-INV-003
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-INV-003
capability: CAP-INV-001
owner: domain
---

# Task: Calculate NAV and member ownership

## Goal

Derive NAV, unit price, member attributable value, and ownership percentage from
caller-supplied valuation totals and currency-matched liabilities.

## Acceptance Criteria

- [x] Accept caller-supplied asset totals using Decimal arithmetic.
- [x] Aggregate recorded liabilities by currency when constructing a valuation.
- [x] Calculate `NAV = assets - liabilities`.
- [x] Calculate unit price from NAV and units outstanding.
- [x] Derive member attributable value and ownership percentage from supplied units.
- [x] Add tests for fractional values, invalid inputs, and currency-matched liability totals.

## Planned Changes

- `src/tontine/investments/`
- `tests/investments/`

## Validation

```text
uv run pytest tests/investments/test_valuation.py
```

## Completion Notes

Implemented Decimal-based NAV, unit-price, member-value, and ownership calculations from caller-supplied totals, with liability aggregation available through `LiabilityRegistry`.
