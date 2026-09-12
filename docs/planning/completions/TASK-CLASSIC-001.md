---
task: TASK-CLASSIC-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-CLASSIC-001

## Outcome

Implemented deterministic classic tontine rotation and Decimal expected-payout calculation.

## Acceptance Criteria Evidence

- [x] Rotation order contains unique active member identifiers.
- [x] Missing and duplicate active members are rejected.
- [x] One-based cycle recipient selection wraps deterministically.
- [x] Expected payout is the exact Decimal sum of contributions.
- [x] Tests cover the JPY 30,000 five-member example.

## Validation

```text
uv run pytest tests/classic/test_rotation.py && uv run ruff check src/tontine/classic tests/classic && uv run mypy src/tontine/classic
```

Result: 3 tests passed; Ruff and mypy passed.

## Files Changed

- `src/tontine/classic/__init__.py`
- `tests/classic/test_rotation.py`
- `docs/planning/tasks/TASK-CLASSIC-001.md`
