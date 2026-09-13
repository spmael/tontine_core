---
task: TASK-CON-002
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-CON-002

## Outcome

Implemented contribution recording, deterministic status classification, duplicate protection, explicit adjustment, and Decimal totals.

## Acceptance Criteria Evidence

- [x] Records include member, cycle, expected amount, actual amount, payment timestamp, status, external reference, and notes.
- [x] Pending, paid, partial, late, and missed states are derived deterministically using the cycle timezone.
- [x] Late and missed contributions can assess a fixed penalty with an explicit currency, unpaid status, and default common-reserve destination.
- [x] Expected, received, and outstanding totals use Decimal arithmetic.
- [x] Duplicate records raise `DuplicateContributionError` unless `adjustment=True` is supplied.
- [x] Focused tests cover the first vertical slice and timezone-aware status behavior.

## Validation

```text
uv run pytest tests/contributions/test_contribution_recording.py
```

Result: 4 tests passed.

## Files Changed

- `src/tontine/contributions/__init__.py`
- `src/tontine/exceptions.py`
- `tests/contributions/test_contribution_recording.py`
- `docs/planning/tasks/TASK-CON-002.md`

## Gaps and Follow-up

No gaps for this task. Broader capability validation is recorded with TASK-CON-003.
