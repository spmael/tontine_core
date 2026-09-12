---
task: TASK-CLASSIC-002
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-CLASSIC-002

## Outcome

Implemented immutable classic payout records with historical recipient provenance and duplicate cycle protection.

## Acceptance Criteria Evidence

- [x] Records contain recipient, cycle, amount, currency, timestamp, and source event.
- [x] Duplicate payouts for the same cycle raise `DuplicatePayoutError`.
- [x] Payout records preserve the recipient selected at recording time.
- [x] No payment initiation or external custody behavior is included.

## Validation

```text
uv run pytest tests/classic/test_payouts.py
```

Result: 2 tests passed.

## Files Changed

- `src/tontine/classic/__init__.py`
- `src/tontine/exceptions.py`
- `tests/classic/test_payouts.py`
- `docs/planning/tasks/TASK-CLASSIC-002.md`
