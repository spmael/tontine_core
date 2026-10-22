---
id: TASK-API-003
status: shipped
started: 2026-10-12
completed: 2026-10-12
adr_refs: []
requirements:
  - NFR-API-001
capability: CAP-API-002
owner: package-boundary
---

# Task: Standardize missing-record domain errors

## Goal

Replace public bare `KeyError` missing-record failures with a documented
framework-independent domain exception.

## Context

The existing repository protocols and repository-boundary documentation specify
`KeyError` for missing records. The project owner selected a domain-only error
contract for CAP-API-002, so this change is intentionally breaking for callers
that catch `KeyError`.

## Acceptance Criteria

- [x] Define and document a missing-record exception under the existing domain
  error hierarchy, with enough context to identify the missing record.
- [x] Raise that domain exception consistently for expected missing-record
  lookups, including repository retrieval and ledger correction references.
- [x] Keep invalid-input and duplicate-record failures distinct from missing
  records; do not convert unrelated internal `KeyError` conditions.
- [x] Update repository protocol docstrings and repository-boundary documentation
  to describe the new contract and its compatibility impact.
- [x] Update tests to assert the domain exception and verify it is not exposed as
  `KeyError` for these public missing-record cases.

## Planned Changes

- `src/tontine/exceptions.py`
- `src/tontine/repositories/`
- `src/tontine/groups/`
- `src/tontine/accounts/`
- `src/tontine/contributions/`
- `src/tontine/ledger/`
- `src/tontine/governance/`
- `src/tontine/investments/`
- `docs/architecture/repository-boundaries.md`
- Relevant tests under `tests/`

## Validation

```text
uv run pytest tests/repositories tests/groups/test_group_repository.py tests/accounts/test_account_registry.py tests/contributions/test_contribution_recording.py tests/ledger/test_ledger_corrections.py tests/governance/test_governance.py tests/investments/test_allocation_schedule.py
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

<What changed, evidence produced, and any remaining gap.>
