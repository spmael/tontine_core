---
id: TASK-API-004
status: ready
started: null
completed: null
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

- [ ] Update public datetime validation errors to identify the exact field or
  parameter that is naive.
- [ ] Explain how to supply a timezone-aware value, without converting or
  assuming a timezone for naive inputs.
- [ ] Preserve acceptance of valid timezone-aware inputs and existing timestamp
  semantics.
- [ ] Add focused tests for naive inputs, aware inputs, and actionable message
  content across affected public APIs.
- [ ] Update public docstrings where datetime inputs or their timezone
  requirements need clarification.

## Planned Changes

- `src/tontine/contributions/`
- `src/tontine/classic/`
- `src/tontine/ledger/`
- `src/tontine/investments/`
- `src/tontine/governance/`
- `src/tontine/audit/`
- Relevant tests under `tests/`

## Validation

```text
uv run pytest tests/contributions tests/classic tests/ledger tests/investments tests/governance tests/audit
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

<What changed, evidence produced, and any remaining gap.>
