---
id: TASK-GROUP-003
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-GRP-001
  - FR-GRP-002
  - FR-GRP-003
  - FR-GRP-004
capability: CAP-GROUP-001
owner: domain
---

# Task: Add in-memory repository behavior

## Goal

Provide a simple in-memory store for tontines and members so the domain can be
loaded and queried without a framework or database adapter.

## Acceptance Criteria

- [x] Repository methods support adding and retrieving tontines by identifier.
- [x] Repository methods support adding and retrieving members by identifier.
- [x] Duplicate group identifiers are rejected.
- [x] The repository exposes deterministic, in-memory domain behavior.
- [x] Unit tests cover repository add/retrieve and duplicate rejection.

## Planned Changes

- `src/tontine/groups/`
- `src/tontine/members/`
- `tests/groups/`
- `tests/members/`

## Validation

```text
uv run pytest tests/groups tests/members
```

## Completion Notes

The repository adds and fetches tontines and members in memory, enforces duplicate group IDs, and keeps the domain model isolated from any persistence framework.
