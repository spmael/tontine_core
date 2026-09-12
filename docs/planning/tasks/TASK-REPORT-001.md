---
id: TASK-REPORT-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-RPT-001
  - FR-RPT-003
capability: CAP-REPORT-001
owner: reporting
---

# Task: Define structured member statements

## Goal

Expose an immutable member statement containing contribution, payout, and
investment ownership information without presentation rendering.

## Acceptance Criteria

- [x] Define an immutable structured member statement.
- [x] Include member information and contribution history.
- [x] Include outstanding contributions and supplied penalties when applicable.
- [x] Include payouts received, investment units, ownership, and attributable value.
- [x] Preserve Decimal amounts and explicit currencies.
- [x] Add tests using JPY, XAF, and fractional EUR values.

## Planned Changes

- `src/tontine/reporting/`
- `tests/reporting/`

## Validation

```text
uv run pytest tests/reporting/test_member_statement.py
```

## Completion Notes

Implemented immutable member statements with contribution history, outstanding totals, penalties, payouts, investment units, ownership, attributable value, and explicit currencies.
