---
id: TASK-INV-002
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-INV-002
capability: CAP-INV-001
owner: domain
---

# Task: Record investment activity and valuations

## Goal

Record cash balances, asset purchases, sales, income, fees, and manual valuation
updates without executing investments or retrieving market data.

## Acceptance Criteria

- [x] Record purchase and sale transactions with Decimal amounts and provenance.
- [x] Record income and fees explicitly.
- [x] Record manual asset valuations with source and effective date.
- [x] Reject mutation of recorded activity.
- [x] Add tests for activity types and duplicate-event protection.

## Planned Changes

- `src/tontine/investments/`
- `tests/investments/`

## Validation

```text
uv run pytest tests/investments/test_activity.py
```

## Completion Notes

Implemented immutable purchase, sale, income, and fee activity records with Decimal amounts, timestamped provenance, supplied sources, and duplicate event protection. No investment execution or market-data retrieval exists in the core.
