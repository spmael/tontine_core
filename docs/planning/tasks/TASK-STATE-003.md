---
id: TASK-STATE-003
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

# Task: Snapshot hybrid arrears registry state

## Goal

Capture and restore arrears records and their subsequent payments, elections,
forfeitures, waivers, and offsets deterministically.

## Context

ADR-007: restore typed immutable records directly instead of replaying
undocumented mutation sequences. This registry interacts with allocation and
member-unit state, so its restored references must remain consistent.

## Acceptance Criteria

- [x] Snapshot all arrears records, payment applications, elections,
  forfeitures, waivers, offsets, exit offsets, closed-cycle identities, and
  audit provenance required to continue registry operations.
- [x] Restore exact record histories and derived arrears balances without
  replaying cycle-closing or payment mutation workflows.
- [x] Reject unsupported schemas, duplicate identifiers, broken references,
  inconsistent event ordering, and invalid closure state.
- [x] Preserve post-restore ability to record valid elections, payments, and
  offsets with the supplied allocation and unit-ledger dependencies.
- [x] Cover valid round trips, future operations, tampered snapshots, and public
  imports.

## Planned Changes

- `src/tontine/hybrid/arrears.py`
- `src/tontine/hybrid/arrears_snapshots.py`
- `tests/hybrid/test_state_snapshots.py`

## Validation

```text
uv run pytest tests/hybrid
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Shipped after TASK-STATE-001 and TASK-STATE-002.
