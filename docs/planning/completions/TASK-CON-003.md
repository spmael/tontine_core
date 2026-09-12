---
task: TASK-CON-003
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-CON-003

## Outcome

Added cycle-level outstanding contribution projections derived from expected and recorded Decimal amounts.

## Acceptance Criteria Evidence

- [x] Cycles expose expected, received, and outstanding totals.
- [x] Outstanding totals are clamped at zero when receipts exceed expectations.
- [x] Tests cover pending records, fractional Decimal amounts, and outstanding totals.

## Validation

```text
uv run pytest tests/contributions/test_contribution_recording.py
```

Result: 3 tests passed.

## Files Changed

- `src/tontine/contributions/__init__.py`
- `tests/contributions/test_contribution_recording.py`
- `docs/planning/tasks/TASK-CON-003.md`

## Gaps and Follow-up

None for the current contribution capability scope.
