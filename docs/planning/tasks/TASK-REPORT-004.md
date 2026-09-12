---
id: TASK-REPORT-004
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-RPT-001
  - FR-RPT-002
  - FR-RPT-003
  - NFR-DOC-001
  - NFR-TEST-001
capability: CAP-REPORT-001
owner: reporting
---

# Task: Add reporting tests, examples, and rendering boundary documentation

## Goal

Protect deterministic reporting behavior and document that presentation
rendering belongs to consuming applications.

## Acceptance Criteria

- [x] Add reporting tests without a database, web framework, or network.
- [x] Add practical examples for member and group statements.
- [x] Document PDF, Excel, HTML, and web rendering as external concerns.
- [x] Test stable public imports and concise report docstrings.
- [x] Verify report values are derived from supplied domain records.

## Planned Changes

- `README.md`
- `examples/`
- `src/tontine/reporting/`
- `tests/reporting/`

## Validation

```text
uv run pytest tests/reporting
uv run ruff check src/tontine/reporting tests/reporting
uv run mypy src/tontine/reporting
```

## Completion Notes

Added reporting tests and README documentation showing structured statements as application inputs while keeping presentation adapters outside the core package.
