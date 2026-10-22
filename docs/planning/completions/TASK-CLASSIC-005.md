---
task: TASK-CLASSIC-005
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-CLASSIC-005

## Outcome

Added immutable effective-cycle rotation versions and deterministic schedule
resolution. The latest effective cycle applies, with the highest version number
breaking ties. Adding a version returns a new schedule and preserves previous
schedule instances.

## Acceptance Criteria Evidence

- [x] `ClassicRotationVersion` validates its version, cycle, order, and source
  event in `src/tontine/classic/rotation_schedule.py`.
- [x] `ClassicRotationSchedule.version_for_cycle` resolves by effective cycle
  and version number.
- [x] Tests cover missing versions, invalid cycles, duplicate versions, tie
  resolution, and preservation of previous schedules.
- [x] Public imports are tested through `tontine.classic`.

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
- `docs/planning/tasks/TASK-CLASSIC-005.md`
- `docs/planning/completions/TASK-CLASSIC-005.md`

## Gaps and Follow-up

- Durable persistence is outside the core package.
