---
id: TASK-GROUP-001
status: ready
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

- [ ] Group, member, role, and membership status values are explicit and typed.
- [ ] Invalid currency or identifier values produce domain errors.
- [ ] Public types have concise docstrings.
- [ ] Unit tests cover valid and invalid values.

## Planned Changes

- `src/tontine/groups/`
- `src/tontine/members/`
- `src/tontine/exceptions.py`
- `tests/groups/`
- `tests/members/`

## Validation

```text
python -m pytest tests/groups tests/members
```

## Completion Notes

Not started.
