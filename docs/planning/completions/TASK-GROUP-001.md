---
task: TASK-GROUP-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-GROUP-001

## Outcome

Implemented the core group and membership domain vocabulary for draft tontines, member roles, membership states, and currency validation without introducing framework or persistence adapters.

## Acceptance Criteria Evidence

- [x] Group, member, role, and membership status values are explicit and typed: `GroupStatus`, `MemberRole`, `MembershipStatus`, `GroupId`, `MemberId`, and `CurrencyCode` in `src/tontine/groups/__init__.py` and `src/tontine/members/__init__.py`.
- [x] Invalid currency or identifier values produce domain errors: `InvalidCurrencyError`, duplicate member checks, and identifier validation in `src/tontine/exceptions.py`, `src/tontine/groups/__init__.py`, and `src/tontine/members/__init__.py`.
- [x] Public types have concise docstrings: value object and entity classes contain package-level docstrings and method docstrings.
- [x] Unit tests cover valid and invalid values: `tests/groups/test_group_domain.py` and `tests/members/test_membership.py`.

## Validation

```text
cd /workspaces/tontine_core && uv run pytest && uv run ruff check src tests && uv run mypy src
```

All checks passed.

## Files Changed

- `src/tontine/exceptions.py`
- `src/tontine/groups/__init__.py`
- `src/tontine/members/__init__.py`
- `tests/groups/test_group_domain.py`
- `tests/members/test_membership.py`

## Gaps and Follow-up

- `TASK-GROUP-002` and `TASK-GROUP-003` remain open for the broader group capability implementation and repository behavior.
