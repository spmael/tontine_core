---
id: TASK-REPORT-002
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-RPT-002
  - FR-RPT-003
capability: CAP-REPORT-001
owner: reporting
---

# Task: Define structured group statements

## Goal

Expose an immutable group statement derived from membership, cycles,
contributions, payouts, investments, liabilities, NAV, and proposals.

## Acceptance Criteria

- [x] Include active members and current cycle.
- [x] Include expected, received, and outstanding contributions.
- [x] Include cash balance, investment value, liabilities, and NAV.
- [x] Include historical payouts and pending proposals.
- [x] Derive values from supplied domain records rather than manual report balances.
- [x] Add tests for empty, partial, and complete group data.

## Planned Changes

- `src/tontine/reporting/`
- `tests/reporting/`

## Validation

```text
uv run pytest tests/reporting/test_group_statement.py
```

## Completion Notes

Implemented immutable group statements that derive contribution totals and NAV from supplied records without querying infrastructure or rendering documents.
