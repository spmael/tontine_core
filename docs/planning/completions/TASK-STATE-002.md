---
task: TASK-STATE-002
started: 2026-10-18
completed: 2026-10-18
status: shipped
---

# Completion: Snapshot hybrid allocation registry state

## Outcome

Added `HybridAllocationSnapshot` schema v1 and registry snapshot/restore APIs.
Snapshots preserve resolved and pending allocations, the exact rule version
needed to resolve pending work, reversal and exit-freeze records, and the
registry's audit events in order. Restore validates the supplied unit-ledger
history and rebuilds registry indexes without replaying allocations or audit
mutations.

## Acceptance Criteria Evidence

- [x] Snapshots preserve resolved and pending allocations, pending rule
  provenance, reversals, exit freezes, and audit provenance.
- [x] Restore uses stored outcomes and exact pending rule versions without
  recalculating allocation or reversal outcomes.
- [x] Unsupported schemas, duplicate records, broken reversals, inconsistent
  pending rules, and mismatched unit-event history are rejected.
- [x] Registry and audit-event ordering are retained; external shared audit
  registries are validated rather than replayed.
- [x] Round-trip, pending-resolution, reversal, invalid-state, and public import
  behavior are covered in `tests/hybrid/test_state_snapshots.py`.

## Validation

```text
uv run pytest tests/hybrid/test_state_snapshots.py tests/hybrid
156 passed.

uv run ruff check src/tontine/hybrid/snapshots.py src/tontine/hybrid/allocation_registry.py src/tontine/hybrid/allocation.py src/tontine/hybrid/__init__.py tests/hybrid/test_state_snapshots.py
All checks passed.

uv run ruff format --check src/tontine/hybrid/snapshots.py src/tontine/hybrid/allocation_registry.py src/tontine/hybrid/allocation.py src/tontine/hybrid/__init__.py tests/hybrid/test_state_snapshots.py
All five files already formatted.

uv run mypy src/tontine/hybrid
Success: no issues found in 13 source files.
```

## Files Changed

- `README.md`
- `docs/planning/completions/TASK-STATE-002.md`
- `docs/planning/tasks/TASK-STATE-002.md`
- `src/tontine/hybrid/__init__.py`
- `src/tontine/hybrid/allocation.py`
- `src/tontine/hybrid/allocation_registry.py`
- `src/tontine/hybrid/snapshots.py`
- `tests/hybrid/test_state_snapshots.py`

## Gaps and Follow-up

- Arrears and exit registry snapshots remain in TASK-STATE-003 and
  TASK-STATE-004.
- Rebuildable ledger balance projections remain in TASK-STATE-005.
