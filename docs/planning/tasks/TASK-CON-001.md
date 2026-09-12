---
id: TASK-CON-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-CON-001
  - FR-CON-002
capability: CAP-CON-001
owner: domain
---

# Task: Define contribution rule and cycle vocabulary

## Goal

Define the daily, weekly, and monthly contribution rules and cycle entities using exact monetary
values and explicit dates.

## Acceptance Criteria

- [x] Contribution amounts use `decimal.Decimal`.
- [x] A rule requires amount, currency, frequency (`daily`, `weekly`, or `monthly`), due-date convention, grace period, effective date, and IANA timezone.
- [x] A cycle has an explicit status and due date.
- [x] Invalid or negative amounts are rejected.
- [x] Unit tests cover JPY 30,000 daily, monthly, and weekly contribution rules.

## Planned Changes

- `src/tontine/contributions/`
- `tests/contributions/`

## Validation

```text
python -m pytest tests/contributions
```

## Completion Notes

Implemented daily, weekly, and monthly contribution frequency choices with explicit due-date conventions and IANA timezone validation. Cycle timestamps require timezone-aware datetimes and are classified using the cycle's local calendar date.
