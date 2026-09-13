---
id: TASK-GROUP-002
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

# Task: Implement group and member entities

## Goal

Build the core domain entities for tontines and members with explicit currency,
identity, status, and role validation.

## Acceptance Criteria

- [x] A draft tontine is created with a valid name and ISO currency code.
- [x] Members are added with unique identifiers and explicit roles.
- [x] Members record an explicit membership start date.
- [x] Duplicate member identifiers are rejected at the domain boundary.
- [x] Membership status transitions enforce the valid lifecycle.
- [x] Unit tests cover group creation, member creation, and invalid transitions.

## Planned Changes

- `src/tontine/groups/__init__.py`
- `src/tontine/members/__init__.py`
- `tests/groups/`
- `tests/members/`

## Validation

```text
uv run pytest tests/groups tests/members
```

## Completion Notes

The domain entities are implemented and validated in the core package. They enforce valid group currency codes, member uniqueness, explicit roles, explicit membership start dates, and valid membership transitions across the supported domain lifecycle.
