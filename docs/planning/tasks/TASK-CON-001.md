---
id: TASK-CON-001
status: ready
requirements:
  - FR-CON-001
  - FR-CON-002
capability: CAP-CON-001
owner: domain
---

# Task: Define contribution rule and cycle vocabulary

## Goal

Define the monthly contribution rule and cycle entities using exact monetary
values and explicit dates.

## Acceptance Criteria

- [ ] Contribution amounts use `decimal.Decimal`.
- [ ] A rule requires amount, currency, frequency, due-date convention, grace period, and effective date.
- [ ] A cycle has an explicit status and due date.
- [ ] Invalid or negative amounts are rejected.
- [ ] Unit tests cover JPY 30,000 monthly contributions.

## Planned Changes

- `src/tontine/contributions/`
- `tests/contributions/`

## Validation

```text
python -m pytest tests/contributions
```

## Completion Notes

Not started.
