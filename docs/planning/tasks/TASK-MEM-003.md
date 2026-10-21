---
id: TASK-MEM-003
status: shipped
started: 2026-10-21
completed: 2026-10-21
adr_refs:
  - ADR-008
requirements:
  - FR-MEM-002
capability: CAP-MEM-001
owner: domain
---

# Task: Report responsibility conflicts

## Goal

Model named work responsibilities and report configured incompatible
assignments held by one member within the same scope.

## Context

ADR-008 keeps responsibility names configurable and returns findings without
rejecting assignments or implementing application authorization.

## Acceptance Criteria

- [x] Represent immutable responsibility assignments with member and scope IDs.
- [x] Configure unordered incompatible responsibility pairs.
- [x] Return deterministic findings when one member holds both responsibilities
  in the same scope; do not report cross-scope pairs.
- [x] Keep responsibilities separate from `MemberRole` and authorization.
- [x] Test duplicate/invalid assignments, configurable pairs, same- and
  cross-scope behavior, and public imports.

## Planned Changes

- `src/tontine/members/responsibilities.py`
- `src/tontine/members/__init__.py`
- `tests/members/test_responsibilities.py`

## Validation

```text
uv run pytest tests/members
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Shipped under ADR-008. The checker reports deterministic findings only; it does
not reject assignments or implement authorization.
