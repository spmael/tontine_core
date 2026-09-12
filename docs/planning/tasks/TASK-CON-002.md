---
id: TASK-CON-002
status: backlog
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

- [ ] Record member, cycle, expected amount, actual amount, payment date, status, reference, and notes.
- [ ] Derive pending, paid, partial, late, and missed states deterministically.
- [ ] Report expected, received, and outstanding amounts with `Decimal` arithmetic.
- [ ] Reject duplicate records unless an explicit adjustment is used.
- [ ] Add tests for the first vertical slice scenario.

## Planned Changes

- `src/tontine/contributions/`
- `tests/contributions/`

## Validation

```text
python -m pytest tests/contributions
```

## Completion Notes

Not started.
