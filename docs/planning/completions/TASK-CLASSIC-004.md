---
task: TASK-CLASSIC-004
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-CLASSIC-004

## Outcome

Added seeded classic rotation generation with immutable, verifiable provenance.
The generated order is stable for a given seed and active-member set, and
recipient lookup remains deterministic. Provenance is retained on the rotation
for persistence adapters; durable storage remains outside the core package.

## Acceptance Criteria Evidence

- [x] Generate a rotation from active members and an explicit seed:
  `ClassicRotation.randomized` in `src/tontine/classic/__init__.py`.
- [x] Retain seed, algorithm version, canonical member set, generated order,
  actor, and occurrence time in immutable provenance attached to the rotation.
- [x] Recipient lookup uses the recorded order without randomizing again.
- [x] Reconstruct and verify historical order from recorded provenance.
- [x] Test reproducibility, recipient lookup, invalid inputs, immutability, and
  historical reconstruction in `tests/classic/test_random_rotation.py`.

## Validation

```text
uv run pytest tests/classic
uv run ruff check src/tontine/classic tests/classic
uv run mypy src/tontine/classic/__init__.py
uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
```

Results: 14 classic tests passed; Ruff and mypy reported no issues; all 72
requirements are covered with no undefined references.

## Files Changed

- `BRD.md`
- `src/tontine/classic/__init__.py`
- `tests/classic/test_random_rotation.py`
- `docs/planning/capabilities/CAP-CLASSIC-001.md`
- `docs/planning/tasks/TASK-CLASSIC-004.md`
- `docs/planning/completions/TASK-CLASSIC-004.md`

## Gaps and Follow-up

- Durable storage is intentionally left to persistence adapters.
