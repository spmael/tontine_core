---
task: TASK-API-006
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-API-006

## Outcome

Documented and verified the public error contract: expected missing records
raise `MissingRecordError`; invalid values and state raise `ValueError`; wrong
Python types raise `TypeError`; repository duplicate additions raise
`ValueError`. More specific domain failures use `TontineError` subclasses.
The custom error hierarchy is explicitly exported and framework-independent.

## Acceptance Criteria Evidence

- [x] Error categories and repository duplicate behavior are documented in
  `docs/architecture/repository-boundaries.md`.
- [x] Expected missing lookups are tested as `MissingRecordError`, distinct
  from invalid-value `ValueError` behavior in repository and domain tests.
- [x] `src/tontine/exceptions.py` declares its public exception exports;
  `tests/test_import.py` verifies every exported error is defined by the core
  module and derives directly from `TontineError`. The base derives only from
  Python's built-in `Exception`.
- [x] Pylance's import audit found only `pycountry` and test-only `pytest` as
  external module roots. Source review found no framework-specific imports,
  and `pyproject.toml` declares only `pycountry` as a runtime dependency.

## Validation

```text
uv run pytest tests/test_import.py tests/repositories tests/groups/test_group_repository.py tests/accounts/test_account_registry.py tests/contributions/test_contribution_recording.py tests/ledger/test_ledger_corrections.py tests/governance/test_governance.py tests/investments/test_allocation_schedule.py
uv run pytest
uv run ruff check src tests
uv run mypy src
uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
git diff --check
```

Result: 48 focused tests and the full 130-test suite passed; Ruff and mypy
passed. The import audit found no framework dependency. Traceability reports all
72 requirements covered with no undefined references.

## Files Changed

- `src/tontine/exceptions.py`
- `docs/architecture/repository-boundaries.md`
- `tests/test_import.py`
- `docs/planning/tasks/TASK-API-006.md`
- `docs/planning/capabilities/CAP-API-002.md`
- `docs/planning/completions/TASK-API-006.md`
- `docs/planning/STATUS.md`

## Gaps and Follow-up

- None identified for this task.
