---
id: TASK-STATE-001
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

# Task: Snapshot and rebuild member unit state

## Goal

Record unit issue and redemption events immutably and rebuild member balances
from a versioned snapshot of those events.

## Context

ADR-007: member-unit balances are derived from ordered unit events, not
independently persisted cached values. This is the prerequisite for restoring
hybrid registries without losing their unit projection.

## Acceptance Criteria

- [x] Record immutable, ordered issue/redemption events with stable unique IDs.
- [x] Add an immutable schema-versioned snapshot that stores events rather than
  balances and deterministically rebuilds the ledger.
- [x] Reject unsupported schemas, duplicate event identifiers, and redemptions
  that exceed the balance at their position in the event stream.
- [x] Failed operations do not reserve an event ID or change unit balances.
- [x] Preserve existing unit calculation and ownership behavior and expose the
  snapshot types through `tontine.investments`.
- [x] Document the unit-event snapshot and its role in hybrid state restoration.

## Planned Changes

- `src/tontine/investments/valuation.py`
- `src/tontine/investments/__init__.py`
- `tests/investments/test_units.py`
- `README.md`

## Validation

```text
uv run pytest tests/investments/test_units.py tests/hybrid
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Shipped. The ledger now records typed immutable issue and redemption events,
validates operations before changing event or balance state, and supports a
schema-v1 event snapshot that rebuilds its derived balances. Hybrid callers
retain their existing APIs; the snapshot classes are exported from
`tontine.investments`.
