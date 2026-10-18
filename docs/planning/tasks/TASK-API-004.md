---
id: TASK-API-004
status: shipped
started: 2026-10-12
completed: 2026-10-12
adr_refs: []
requirements:
  - NFR-API-002
capability: CAP-API-002
owner: package-boundary
---

# Task: Make timezone validation errors actionable

## Goal

Make public datetime validation failures identify the offending input and tell
callers how to provide an aware datetime without silently assigning a timezone.

## Context

Public datetime inputs must remain strict about timezone awareness. Error
messages should name the parameter or field and point callers to
`datetime.timezone.utc` or `zoneinfo` when constructing an aware value.

## Acceptance Criteria

- [x] Update public datetime validation errors to identify the exact field or
  parameter that is naive.
- [x] Explain how to supply a timezone-aware value, without converting or
  assuming a timezone for naive inputs.
- [x] Preserve acceptance of valid timezone-aware inputs and existing timestamp
  semantics.
- [x] Add focused tests for naive inputs, aware inputs, and actionable message
  content across affected public APIs.
- [x] Update public docstrings where datetime inputs or their timezone
  requirements need clarification.

## Planned Changes

- `src/tontine/contributions/`
- `src/tontine/classic/`
- `src/tontine/ledger/`
- `src/tontine/investments/`
- `src/tontine/governance/`
- `src/tontine/audit/`
- `src/tontine/_datetime.py`
- Relevant tests under `tests/`

## Validation

```text
uv run pytest tests/contributions tests/classic tests/ledger tests/investments tests/governance tests/audit
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Shared strict datetime validation now names the invalid field and explains how
to construct an aware datetime. Naive values are still rejected; aware values
retain their existing timezone conversion and comparison semantics.
