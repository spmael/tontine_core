---
task: TASK-MEM-002
started: 2026-10-21
completed: 2026-10-21
status: shipped
---

# Completion: Integrate share-level obligations and reporting

## Outcome

Added share-aware contribution-cycle APIs that retain both the share identifier
and owning member identity. Classic rotations can be created from active shares,
and schedules resolve selected share IDs to their owner. Same-currency Decimal
amounts aggregate by member and currency without rounding or conversion.

## Acceptance Criteria Evidence

- [x] Active shares carry expected and received contribution entries through
  `ContributionCycle.add_expected_share_contribution` and
  `record_share_contribution`; `ShareContribution` retains owner identity.
- [x] `ClassicRotation.from_active_shares` and
  `ClassicRotationSchedule.resolve_member_for_cycle` preserve share-keyed
  versions and resolve their member owner.
- [x] `ParticipationShareRegistry.roll_up_amounts` aggregates in explicit
  currency units by member; test covers two shares owned by one person.
- [x] Existing member-keyed methods and rotation versions remain unchanged.
- [x] Tests cover inactive/unknown shares, cycle boundaries, roll-up,
  unchanged historical rotations, and one-vote-per-member governance.

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
- `docs/planning/tasks/TASK-MEM-002.md`
- `src/tontine/classic/__init__.py`
- `src/tontine/classic/rotation_schedule.py`
- `src/tontine/contributions/__init__.py`
- `src/tontine/members/participation.py`
- `tests/members/test_participation.py`

## Gaps and Follow-up

- None for this task. Currency aggregation requires one explicit currency per
  call; callers must aggregate each currency independently.
