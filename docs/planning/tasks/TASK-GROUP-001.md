---
id: TASK-GROUP-001
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

# Task: Define group domain vocabulary

## Goal

Define the typed identifiers, statuses, roles, currency boundary, and domain
exceptions needed by group and membership behavior.

## Acceptance Criteria

- [x] Group, member, role, and membership status values are explicit and typed.
- [x] Invalid currency or identifier values produce domain errors.
- [x] Public types have concise docstrings.
- [x] Unit tests cover valid and invalid values.

## Planned Changes

- `src/tontine/groups/`
- `src/tontine/members/`
- `src/tontine/exceptions.py`
- `tests/groups/`
- `tests/members/`

## Validation

```text
uv run pytest tests/groups tests/members
```

## Completion Notes

The explicit group/member vocabulary and status transitions were implemented in the domain layer, and the new tests confirm valid draft creation, duplicate rejection, currency validation, and allowed membership transitions.
