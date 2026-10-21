---
task: TASK-STATE-004
started: 2026-10-21
completed: 2026-10-21
status: shipped
---

# Completion: Snapshot hybrid exit registry state

## Outcome

Verified and completed the schema-v1 exit snapshot contract. Snapshots retain
all exit status and settlement lines, FIFO queue reports, and audit provenance.
Restore validates the matching allocation freezes, arrears settlement records,
unit redemptions, and proposal provenance without replaying governance approval,
valuation, settlement, or payment workflows. Restored exits can continue through
valid queue and payment status transitions.

## Acceptance Criteria Evidence

- [x] Exit records, settlement details, queue reports, and audit history are
  retained in immutable snapshot values.
- [x] Restore accepts the matching allocation, arrears, and unit-ledger state
  without requiring governance or valuation inputs.
- [x] Unsupported schemas and mismatched proposal, allocation-freeze,
  arrears-settlement, and unit-redemption references are rejected.
- [x] Queue-entry order is retained; a restored payable exit can be recorded as
  externally paid without initiating a transfer.
- [x] Tests cover pending and settled round trips, queue ordering, invalid
  snapshots and dependencies, and the public `HybridExitSnapshot` import.

## Validation

```text
uv run pytest tests/hybrid
168 passed.

uv run ruff check src tests
All checks passed.

uv run ruff format --check src/tontine/hybrid/exit_snapshots.py src/tontine/hybrid/exit.py src/tontine/hybrid/__init__.py tests/hybrid/test_exit.py
4 files already formatted.

uv run mypy src
Success: no issues found in 46 source files.
```

## Files Changed

- `README.md`
- `docs/planning/completions/TASK-STATE-004.md`
- `docs/planning/tasks/TASK-STATE-004.md`
- `src/tontine/hybrid/exit.py`
- `src/tontine/hybrid/exit_snapshots.py`
- `tests/hybrid/test_exit.py`

## Gaps and Follow-up

- Rebuildable ledger balance projections remain in TASK-STATE-005.
