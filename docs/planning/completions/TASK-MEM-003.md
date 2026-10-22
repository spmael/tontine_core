---
task: TASK-MEM-003
started: 2026-10-21
completed: 2026-10-21
status: shipped
---

# Completion: Report responsibility conflicts

## Outcome

Added immutable responsibility assignments and configurable unordered conflict
pairs. The checker returns deterministic findings for incompatible
responsibilities held by one member in one scope. It does not reject assignments
or enforce application permissions.

## Acceptance Criteria Evidence

- [x] Immutable assignment and finding types are in
  `src/tontine/members/responsibilities.py`.
- [x] Conflict pairs are configurable and treated as unordered.
- [x] Findings are scoped to the same member and scope and returned in stable
  order.
- [x] Responsibilities are separate from `MemberRole`; the package adds no
  authentication or authorization behavior.
- [x] Tests cover duplicate IDs, invalid assignments, configured pairs,
  same-/cross-scope behavior, and public imports.

## Validation

```text
uv run pytest
479 passed.

uv run ruff check src tests
All checks passed.

uv run mypy src
Success: no issues found in 49 source files.
```

## Files Changed

- `README.md`
- `docs/architecture/adr/ADR-008-member-shares-and-responsibility-conflicts.md`
- `docs/planning/capabilities/CAP-MEM-001.md`
- `docs/planning/tasks/TASK-MEM-003.md`
- `src/tontine/members/__init__.py`
- `src/tontine/members/responsibilities.py`
- `tests/members/test_responsibilities.py`

## Gaps and Follow-up

- Conflict vocabularies are intentionally caller-configured; the core defines no
  universal set of incompatible responsibility pairs.
