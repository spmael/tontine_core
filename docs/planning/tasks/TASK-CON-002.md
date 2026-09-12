---
id: TASK-CON-002
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-CON-003
  - FR-CON-004
  - FR-CON-005
  - NFR-CAL-001
  - NFR-CAL-002
capability: CAP-CON-001
owner: domain
---

# Task: Record and classify contributions

## Goal

Record contributions and derive their status without processing external payments.

## Acceptance Criteria

- [x] Record member, cycle, expected amount, actual amount, payment date, status, reference, and notes.
- [x] Derive pending, paid, partial, late, and missed states deterministically.
- [x] Report expected, received, and outstanding amounts with `Decimal` arithmetic.
- [x] Reject duplicate records unless an explicit adjustment is used.
- [x] Add tests for the first vertical slice scenario.

## Planned Changes

- `src/tontine/contributions/`
- `tests/contributions/`

## Validation

```text
python -m pytest tests/contributions
```

## Completion Notes

Contribution records now classify payment states from explicit timezone-aware timestamps, reject duplicate records unless adjusted explicitly, and expose Decimal-based expected, received, and outstanding totals.
