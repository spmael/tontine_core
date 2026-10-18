---
task: TASK-GOV-005
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-GOV-005

## Outcome

`GovernanceRegistry.snapshot()` exports schema-versioned immutable state;
`GovernanceRegistry.from_snapshot()` deterministically restores supported
snapshots and rejects unsupported schemas, invalid lifecycle/tally state, and
inconsistent effect or audit provenance. Snapshots preserve shared audit
history order and identify the events owned by the governance registry.

## Acceptance Criteria Evidence

- [x] Snapshot values contain active members, rotation versions and exceptions,
  proposal state and typed effects, rulesets, and audit events.
- [x] Round trips preserve open votes, frozen electorates, approved effects,
  rulesets, and append order of audit records.
- [x] Restore validates schema version, lifecycle/evaluation consistency,
  effect approval provenance, and audit-backed state.
- [x] Public exports and round-trip, unsupported-schema, inconsistent-state,
  and shared-audit tests pass.

## Validation

```text
.venv/bin/python -m pytest tests/governance -q
.venv/bin/ruff check src/tontine/governance tests/governance
.venv/bin/mypy src/tontine/governance
.venv/bin/python -m pytest -q
.venv/bin/ruff check src tests
.venv/bin/mypy src
uv build
```

Results: 27 governance tests and 158 total tests passed; Ruff and mypy reported
no issues; source and wheel distributions built successfully.

## Files Changed

- `src/tontine/governance/snapshots.py`
- `src/tontine/governance/snapshot_validation.py`
- `src/tontine/governance/registry.py`
- `src/tontine/governance/__init__.py`
- `tests/governance/test_effects_and_snapshots.py`
- `BRD.md`
- `docs/planning/tasks/TASK-GOV-005.md`

## Gaps and Follow-up

No task-level gaps remain. Snapshot serialization and durable storage remain
adapter responsibilities.
