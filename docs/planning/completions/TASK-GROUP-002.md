---
task: TASK-GROUP-002
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-GROUP-002

## Outcome

Implemented the core tontine and member entities with validated identifiers, explicit roles, lifecycle states, and duplicate/member transition guards.

## Acceptance Criteria Evidence

- [x] Draft tontine creation uses a valid name and ISO currency code: validated in `src/tontine/groups/__init__.py` and exercised by `tests/groups/test_group_domain.py`.
- [x] Members are added with unique identifiers and explicit roles: `Group.add_member()` enforces uniqueness and stores members by identifier.
- [x] Members store an explicit membership start date: `Member.create()` requires `membership_start_date` and preserves it on the entity.
- [x] Duplicate identifiers are rejected at the domain boundary: `DuplicateMemberError` is raised for repeat member IDs.
- [x] Membership transitions follow the valid lifecycle: `activate()`, `suspend()`, `leave()`, and `remove()` enforce transitions in `src/tontine/members/__init__.py`.
- [x] Unit tests cover group creation, member creation, and invalid transitions: `tests/groups/test_group_domain.py` and `tests/members/test_membership.py`.

## Validation

```text
cd /workspaces/tontine_core && uv run pytest tests/groups tests/members
```

All checks passed.

## Files Changed

- `src/tontine/groups/__init__.py`
- `src/tontine/members/__init__.py`
- `tests/groups/test_group_domain.py`
- `tests/members/test_membership.py`

## Gaps and Follow-up

- `TASK-GROUP-003` remains open for repository-style in-memory persistence behavior and duplicate group-ID handling.
