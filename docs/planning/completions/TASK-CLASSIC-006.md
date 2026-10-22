---
task: TASK-CLASSIC-006
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-CLASSIC-006

## Outcome

Added immutable approved one-cycle recipient overrides. The override changes
only the selected recipient for its cycle; base rotation, payout calculation,
unpaid-contribution eligibility, and adjacent-cycle recipient selection remain
unchanged.

## Acceptance Criteria Evidence

- [x] `ApprovedRotationException` retains cycle, recipient, proposal, approval
  event, and timezone-aware approval time.
- [x] `ClassicRotationSchedule.with_exception` validates one exception per
  cycle and membership in the effective rotation.
- [x] `ClassicRotationSchedule.resolve_cycle` returns both the base rotation
  version and the selected recipient.
- [x] Public API tests verify recipient-only behavior, unchanged payout and
  unpaid policy, validation failures, and restoration on adjacent cycles.

## Validation

```text
uv run pytest tests/classic tests/governance
uv run pytest
uv run ruff check src/tontine/classic tests/classic
uv run mypy src/tontine/classic src/tontine/governance
```

Results: 33 classic/governance tests and all 142 project tests passed; Ruff and
mypy reported no issues.

## Files Changed

- `src/tontine/classic/__init__.py`
- `src/tontine/classic/rotation_schedule.py`
- `tests/classic/test_rotation_schedule.py`
- `BRD.md`
- `docs/architecture/next-version-gap-architecture.md`
- `docs/planning/capabilities/CAP-CLASSIC-002.md`
- `docs/planning/tasks/TASK-CLASSIC-006.md`
- `docs/planning/completions/TASK-CLASSIC-006.md`

## Gaps and Follow-up

- Proposal creation, voting, and production of approved exception effects remain
  in `CAP-GOV-002`; the classic schedule consumes an explicit approved-effect
  record without replaying governance history.
