---
id: TASK-CLASSIC-005
status: shipped
started: 2026-10-18
completed: 2026-10-18
requirements:
  - FR-CLS-005
capability: CAP-CLASSIC-002
owner: domain
---

# Task: Add immutable effective-cycle rotation versions

## Goal

Resolve the applicable classic rotation order for a cycle from immutable
effective-cycle versions without replaying governance history.

## Context

The latest effective cycle applies. If multiple versions share that effective
cycle, the highest version number wins. Schedule updates return new schedule
values, preserving prior schedule instances.

## Acceptance Criteria

- [x] Add validated, immutable rotation version values with explicit effective
  cycles and source-event provenance.
- [x] Resolve the latest applicable version and deterministically break equal
  effective-cycle ties by version number.
- [x] Reject duplicate version numbers, invalid cycles, and invalid rotation
  orders.
- [x] Preserve older schedule values and earlier cycle resolution when later
  versions are added.
- [x] Test the public classic API without constructing or replaying governance.

## Planned Changes

- `src/tontine/classic/`
- `tests/classic/test_rotation_schedule.py`

## Validation

```text
uv run pytest tests/classic tests/governance
uv run ruff check src/tontine/classic tests/classic
uv run mypy src/tontine/classic src/tontine/governance
```

## Completion Notes

See `docs/planning/completions/TASK-CLASSIC-005.md`.
