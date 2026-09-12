---
task: TASK-INV-006
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-INV-006

## Outcome

Implemented recurring, versioned allocation-rule scheduling with explicit lifecycle boundaries and audit integration.

## Acceptance Criteria Evidence

- [x] Allocation rules can recur automatically across eligible cycles.
- [x] One-cycle or bounded behavior is supported with an end cycle.
- [x] Rules can be cancelled or replaced from an explicit effective cycle.
- [x] Historical rules remain immutable and resolvable for prior cycles.
- [x] Schedule changes optionally emit canonical `AuditEvent` records.
- [x] Tests cover recurring, ended, cancelled, replaced, duplicate, and invalid-cycle behavior.

## Validation

```text
uv run pytest tests/investments/test_allocation_schedule.py && uv run ruff check src/tontine/investments tests/investments/test_allocation_schedule.py && uv run mypy src/tontine/investments
```

Result: 3 tests passed; Ruff and mypy passed.

## Files Changed

- `src/tontine/investments/__init__.py`
- `tests/investments/test_allocation_schedule.py`
- `docs/planning/tasks/TASK-INV-006.md`

## Gaps and Follow-up

Per-cycle allocation amount calculation and ledger posting remain separate follow-up work; this task governs rule recurrence and selection.