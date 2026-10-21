---
task: TASK-MEM-001
started: 2026-10-21
completed: 2026-10-21
status: shipped
---

# Completion: Define stable participation shares

## Outcome

Added immutable share records with stable share and member identifiers, explicit
effective and retirement cycles, and deterministic registry lookups. A share is
active from its effective cycle through the cycle before retirement.

## Acceptance Criteria Evidence

- [x] Stable immutable share records: `ParticipationShare` and
  `ParticipationShareId` in `src/tontine/members/participation.py`.
- [x] Cycle boundaries and deterministic listing: `is_active_for`,
  `shares_for_cycle`, and retirement boundary tests.
- [x] Duplicate/malformed identifiers rejected without replacement:
  duplicate-registration and invalid-record tests.
- [x] Public imports and person-based governance documented in
  `src/tontine/members/__init__.py` and `README.md`; vote eligibility uses
  member IDs in the integration test.

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
- `docs/planning/tasks/TASK-MEM-001.md`
- `src/tontine/members/__init__.py`
- `src/tontine/members/identity.py`
- `src/tontine/members/participation.py`
- `tests/members/test_participation.py`

## Gaps and Follow-up

- None for this task.
