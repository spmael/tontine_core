---
id: TASK-GOV-005
status: shipped
started: 2026-10-18
completed: 2026-10-18
requirements:
  - FR-GOV-005
  - FR-GOV-008
  - FR-GOV-011
capability: CAP-GOV-002
adr_refs:
  - ADR-004
owner: domain
---

# Task: Add versioned governance snapshots

## Goal

Export and restore governance registry state through a versioned immutable
snapshot without replaying undocumented public mutations.

## Context

Snapshot schema version 1 contains active membership, immutable rotation
versions and exceptions, proposal effects and lifecycle state, rulesets, and
audit history. Persistence adapters remain outside the package.

## Acceptance Criteria

- [x] Export complete registry state into an immutable versioned snapshot.
- [x] Rehydrate a registry deterministically from a supported snapshot version.
- [x] Reject unsupported schema versions and internally inconsistent state
  explicitly.
- [x] Preserve open proposal votes, frozen electorates, approved effects,
  rulesets, and audit event order after rehydration.
- [x] Test round trips, invalid snapshots, and public imports.

## Planned Changes

- `src/tontine/governance/`
- `tests/governance/`

## Validation

```text
uv run pytest tests/governance
uv run ruff check src/tontine/governance tests/governance
uv run mypy src/tontine/governance
```

## Completion Notes

Depends on the proposal and effect types from `TASK-GOV-003` and
`TASK-GOV-004`. Schema version 1 captures current membership, rotation versions
and exceptions, proposal state and typed effects, rulesets, and full audit
history with registry-owned event identifiers for provenance checks.
