---
id: TASK-CON-003
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-CON-004
capability: CAP-CON-001
owner: domain
---

# Task: Add outstanding-contribution projection and tests

## Goal

Expose deterministic outstanding contribution totals derived from expected and recorded Decimal amounts.

## Acceptance Criteria

- [x] Expected, received, and outstanding totals are available from a cycle.
- [x] Outstanding totals never become negative when recorded amounts exceed expectations.
- [x] Tests cover pending contributions and Decimal precision.

## Planned Changes

- `src/tontine/contributions/`
- `tests/contributions/`

## Validation

```text
uv run pytest tests/contributions
```

## Completion Notes

Cycle projections derive totals from expected and recorded contributions using Decimal arithmetic; tests cover pending records and fractional amounts such as 30,000.10.
