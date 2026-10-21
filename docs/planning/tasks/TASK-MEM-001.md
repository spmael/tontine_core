---
id: TASK-MEM-001
status: shipped
started: 2026-10-21
completed: 2026-10-21
adr_refs:
  - ADR-008
requirements:
  - FR-MEM-001
capability: CAP-MEM-001
owner: domain
---

# Task: Define stable participation shares

## Goal

Represent a member's distinct participation shares with stable identifiers and
explicit cycle-effective lifecycles.

## Context

ADR-008 treats shares as separate immutable identity records. Adding or retiring
a share applies from an explicit cycle and does not rewrite existing rotation
versions.

## Acceptance Criteria

- [x] Add immutable share records with stable share and owning member IDs.
- [x] Validate effective and retirement cycle boundaries and expose active shares
  in deterministic order.
- [x] Reject duplicate shares and malformed member/share identifiers without
  mutation.
- [x] Expose public imports and document that governance remains person-based.

## Planned Changes

- `src/tontine/members/participation.py`
- `src/tontine/members/__init__.py`
- `tests/members/test_participation.py`
- `README.md`

## Validation

```text
uv run pytest tests/members
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Shipped under ADR-008. Stable share records are exposed through the member
package, active-cycle listing is deterministic, and share retirement does not
mutate previously constructed rotation versions.
