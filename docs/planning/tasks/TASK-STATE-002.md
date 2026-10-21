---
id: TASK-STATE-002
status: shipped
started: 2026-10-18
completed: 2026-10-18
adr_refs:
  - ADR-007
requirements:
  - FR-API-004
capability: CAP-STATE-001
owner: domain
---

# Task: Snapshot hybrid allocation registry state

## Goal

Capture and restore resolved and pending allocations, reversals, and allocation
freeze state using a schema-versioned immutable snapshot.

## Context

ADR-007 and TASK-STATE-001: hybrid state uses versioned snapshots, and member
unit state is rebuilt from the ordered unit-event snapshot.

## Acceptance Criteria

- [x] Snapshot resolved allocations, pending allocations and their effective
  rule versions, reversals, and recorded member exit freezes.
- [x] Restore into a fresh registry without recalculating any recorded
  allocation or reversal outcome.
- [x] Reject unsupported schemas, duplicate identifiers, broken reversal
  references, and inconsistent pending-rule provenance.
- [x] Preserve stable record ordering and audit provenance without replaying
  audit events as state mutations.
- [x] Cover snapshot round trips, pending-resolution after restore, reversals,
  invalid state, and public imports.

## Planned Changes

- `src/tontine/hybrid/allocation_registry.py`
- `src/tontine/hybrid/snapshots.py`
- `src/tontine/hybrid/allocation.py`
- `src/tontine/hybrid/__init__.py`
- `tests/hybrid/test_state_snapshots.py`

## Validation

```text
uv run pytest tests/hybrid
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Shipped after TASK-STATE-001 established the member-unit event snapshot.
