---
id: TASK-INV-007
status: shipped
started: 2026-10-18
completed: 2026-10-18
requirements:
  - FR-INV-006
capability: CAP-INV-002
owner: domain
---

# Task: Represent valuation before unit issuance

## Goal

Make zero units outstanding a valid valuation state per ADR-005, and split the
investments module by capability to keep files below the size guideline.

## Acceptance Criteria

- [x] Split `tontine.investments` into allocation, asset, activity, valuation,
  and FX modules while preserving public imports.
- [x] Accept zero units outstanding and expose `has_units_outstanding`.
- [x] Return `None` for unit price, member value, and ownership percentage when
  no units are outstanding; keep NAV derived.
- [x] Report zero ownership and value in `InvestmentSummary.from_valuation` for
  the no-units state.
- [x] Add tests for the no-units state and reporting.

## Planned Changes

- `src/tontine/investments/`
- `src/tontine/reporting/__init__.py`
- `tests/investments/test_valuation.py`
- `tests/reporting/test_member_statement.py`

## Validation

```text
uv run pytest tests/investments tests/reporting
uv run mypy src
```

## Completion Notes

See [completion record](../completions/TASK-INV-007.md).
