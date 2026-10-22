---
id: TASK-API-006
status: shipped
started: 2026-10-18
completed: 2026-10-18
adr_refs: []
requirements:
  - NFR-API-001
capability: CAP-API-002
owner: package-boundary
---

# Task: Verify and document the public error contract

## Goal

Make the public domain error contract explicit and protect its framework
independence with executable tests.

## Context

CAP-API-002 requires callers to distinguish missing records from invalid input
and requires public error types to remain framework-independent. TASK-API-003
implemented the missing-record behavior; this task audits and records the
broader contract.

## Acceptance Criteria

- [x] Document the public exceptions for missing records, invalid values,
  incorrect Python types, and repository duplicates.
- [x] Verify expected missing-record lookups are translated to
  `MissingRecordError` and invalid inputs remain distinct.
- [x] Explicitly export the domain exception hierarchy and test that every
  exported domain exception derives only from `TontineError`, whose base is
  Python's built-in `Exception`.
- [x] Verify the core has no framework-specific exception imports or runtime
  dependencies.

## Planned Changes

- `src/tontine/exceptions.py`
- `docs/architecture/repository-boundaries.md`
- `tests/test_import.py`
- Relevant existing boundary and invalid-input tests

## Validation

```text
uv run pytest tests/test_import.py tests/repositories tests/groups/test_group_repository.py tests/accounts/test_account_registry.py tests/contributions/test_contribution_recording.py tests/ledger/test_ledger_corrections.py tests/governance/test_governance.py tests/investments/test_allocation_schedule.py
uv run pytest
uv run ruff check src tests
uv run mypy src
uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
git diff --check
```

## Completion Notes

Documented the public distinction between missing records, invalid values,
incorrect Python types, and duplicate repository records. The expected
missing-record paths use `MissingRecordError`; existing focused tests exercise
invalid values and duplicate cases separately. The explicit `tontine.exceptions`
export list and regression test protect the framework-independent exception
hierarchy. Source and package-manifest review found no framework imports or
framework runtime dependencies.
