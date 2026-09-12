---
id: TASK-LEDGER-002
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-LDG-001
  - FR-LDG-002
capability: CAP-LEDGER-001
owner: domain
---

# Task: Implement balanced posting and derived balances

## Goal

Post balanced double-entry journals and derive account balances from recorded
entries rather than maintaining mutable balance fields.

## Acceptance Criteria

- [x] Require at least one debit and one credit entry.
- [x] Reject journals whose debit and credit totals do not balance.
- [x] Derive account balances from posted entries.
- [x] Keep all monetary calculations in Decimal arithmetic.
- [x] Add tests for balanced, unbalanced, and derived-balance scenarios.

## Planned Changes

- `src/tontine/ledger/`
- `tests/ledger/`

## Validation

```text
uv run pytest tests/ledger/test_ledger_posting.py
```

## Completion Notes

Implemented balanced double-entry posting and derived balances from immutable journal entries. No manually maintained balance fields or external payment operations were introduced.
