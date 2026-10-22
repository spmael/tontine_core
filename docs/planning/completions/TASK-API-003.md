---
task: TASK-API-003
status: shipped
started: 2026-10-12
completed: 2026-10-12
---

# Completion: TASK-API-003

## Outcome

Added `MissingRecordError` as a framework-independent `TontineError` subclass
and applied it consistently to expected missing-record lookups. The error is
deliberately not a `KeyError`, as selected by the project owner; this is a
breaking change for consumers that caught `KeyError`.

## Acceptance Criteria Evidence

- [x] Define and document a missing-record exception under the domain error
  hierarchy: `src/tontine/exceptions.py`; exported at `tontine.MissingRecordError`.
- [x] Raise it consistently for expected lookup failures: repositories, group
  and account registries, contribution records, ledger corrections, governance,
  and investment allocation schedules.
- [x] Keep invalid-input and duplicate-record failures distinct; only
  missing-record paths use `MissingRecordError`.
- [x] Update repository protocol docs and
  `docs/architecture/repository-boundaries.md` with the new contract and
  compatibility impact.
- [x] Update tests to assert the domain exception and verify it is not a
  `KeyError`: `tests/test_import.py` and affected domain tests.

## Validation

```text
uv run pytest tests/repositories tests/groups/test_group_repository.py tests/accounts/test_account_registry.py tests/contributions/test_contribution_recording.py tests/ledger/test_ledger_corrections.py tests/governance/test_governance.py tests/investments/test_allocation_schedule.py tests/test_import.py
uv run pytest
uv run ruff check src tests
uv run mypy src
git diff --check
```

Result: focused suite passed (38 tests); full suite passed (120 tests); Ruff,
mypy, and diff checks passed. Search confirmed no remaining explicit
`KeyError` raises, protocol contracts, or `pytest.raises(KeyError)` assertions
under `src/tontine` and `tests`.

## Files Changed

- `src/tontine/exceptions.py`
- `src/tontine/__init__.py`
- `src/tontine/accounts/`
- `src/tontine/contributions/`
- `src/tontine/governance/`
- `src/tontine/groups/`
- `src/tontine/investments/`
- `src/tontine/ledger/`
- `src/tontine/repositories/`
- `tests/`
- `docs/architecture/repository-boundaries.md`
- `docs/planning/capabilities/CAP-API-002.md`
- `docs/planning/tasks/TASK-API-003.md`

## Gaps and Follow-up

- TASK-API-004 remains responsible for actionable timezone validation errors.
- TASK-API-005 remains responsible for explicit audit occurrence times.
- Consumers catching `KeyError` for missing domain records must migrate to
  `MissingRecordError`.
