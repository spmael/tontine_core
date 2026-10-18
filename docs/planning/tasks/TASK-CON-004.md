---
id: TASK-CON-004
status: shipped
started: 2026-10-18
completed: 2026-10-18
adr_refs: []
requirements:
  - FR-CON-007
  - NFR-API-002
capability: CAP-CON-002
owner: domain
---

# Task: Propagate contribution penalty destinations

## Goal

Carry an effective contribution rule's configured penalty destination into
assessments and preserve explicitly supplied occurrence timestamps.

## Context

Penalty assessments default to `COMMON_RESERVE` for compatibility, but an
effective contribution rule must be able to select any supported destination.
Public datetime inputs must retain actionable timezone-awareness validation,
and explicit mutation times must be preserved.

## Acceptance Criteria

- [x] Contribution rules accept and validate a penalty destination, defaulting
  to `COMMON_RESERVE`.
- [x] Rule-created cycles carry penalty amount, currency, grace period, and
  destination into late and missed penalty assessments through the public API.
- [x] Naive public datetime inputs identify the field and explain how to provide
  an aware value.
- [x] Explicit payment and assessment times are retained on their records.
- [x] BRD and completion evidence describe the behavior and executable checks.

## Planned Changes

- `src/tontine/contributions/`
- `src/tontine/__init__.py`
- `tests/contributions/`
- `tests/test_public_api.py`
- `BRD.md`

## Validation

```text
uv run pytest
uv run ruff check src tests
uv run mypy src
uv build
uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
uv run python .agents/skills/pdlc/scripts/status.py docs/planning
```

## Completion Notes

All five configured destinations flow from rules through the public cycle
factory into late and missed penalties. Existing `COMMON_RESERVE` defaults and
explicit, timezone-aware occurrence timestamps are preserved. Full test,
lint, type-check, and build validation passed.
