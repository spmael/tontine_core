---
task: TASK-CLASSIC-003
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-CLASSIC-003

## Outcome

Implemented configurable unpaid-contribution payout eligibility.

## Acceptance Criteria Evidence

- [x] `UnpaidContributionPolicy` defines explicit `ALLOW` and `DENY` choices.
- [x] Positive outstanding contributions require a policy.
- [x] Implicit decisions are rejected when contributions remain outstanding.
- [x] Tests cover allowed, denied, and missing-policy decisions.

## Validation

```text
uv run pytest tests/classic/test_unpaid_policy.py
```

Result: 2 tests passed.

## Files Changed

- `src/tontine/classic/__init__.py`
- `tests/classic/test_unpaid_policy.py`
- `docs/planning/tasks/TASK-CLASSIC-003.md`
