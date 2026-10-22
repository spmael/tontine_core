---
task: TASK-STATE-003
started: 2026-10-18
completed: 2026-10-18
status: shipped
---

# Completion: Snapshot hybrid arrears registry state

## Outcome

Added a schema-v1 arrears snapshot covering arrears records, payments,
elections, forfeitures, waivers, unit offsets, exit setoffs, closed-cycle
identities, settled exits, and audit events. Restore rebuilds derived indexes
and validates event references and remaining balances. It also verifies
catch-up payment allocations and unit redemption events against the restored
allocation and unit-ledger registries.

## Acceptance Criteria Evidence

- [x] All arrears history collections, closure state, settled exit identities,
  and registry audit events are stored in stable order.
- [x] Restore derives balances and registry indexes from immutable records
  without replaying public mutation workflows.
- [x] Unsupported schemas, duplicate IDs, invalid references, over-applied
  histories, and inconsistent closed-cycle records are rejected.
- [x] Future elections, payments, and unit offsets work after restoration when
  supplied with matching allocation and unit-ledger state.
- [x] Tests cover round trips, penalties and waivers, disabled catch-up
  forfeitures, exit setoffs, cross-registry references, invalid snapshots, and
  public imports.

## Validation

```text
uv run pytest tests/hybrid/test_state_snapshots.py tests/hybrid
162 passed.

uv run ruff check src/tontine/hybrid/arrears_snapshots.py src/tontine/hybrid/arrears.py src/tontine/hybrid/__init__.py tests/hybrid/test_state_snapshots.py
All checks passed.

uv run ruff format --check src/tontine/hybrid/arrears_snapshots.py src/tontine/hybrid/arrears.py src/tontine/hybrid/__init__.py tests/hybrid/test_state_snapshots.py
All four files already formatted.

uv run mypy src/tontine/hybrid
Success: no issues found in 14 source files.
```

## Files Changed

- `README.md`
- `docs/planning/completions/TASK-STATE-003.md`
- `docs/planning/tasks/TASK-STATE-003.md`
- `src/tontine/hybrid/__init__.py`
- `src/tontine/hybrid/arrears.py`
- `src/tontine/hybrid/arrears_snapshots.py`
- `tests/hybrid/test_state_snapshots.py`

## Gaps and Follow-up

- Exit-registry snapshots remain in TASK-STATE-004.
- Rebuildable ledger balance projections remain in TASK-STATE-005.
