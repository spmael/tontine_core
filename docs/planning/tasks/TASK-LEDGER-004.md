---
id: TASK-LEDGER-004
status: shipped
started: 2026-10-21
completed: 2026-10-21
adr_refs:
  - ADR-007
requirements:
  - FR-LDG-005
  - NFR-PERF-001
capability: CAP-LEDGER-002
owner: domain
---

# Task: Add indexed point-in-time ledger balances

## Goal

Query account/currency balances at an optional historical instant without
replaying all journals for each read.

## Context

FR-LDG-005 includes only journals with `recorded_at` on or before the requested
timezone-aware instant. Reversals and adjustments affect historical balances
from their own recorded time; immutable journals remain authoritative.

## Acceptance Criteria

- [x] Add an optional timezone-aware `as_of` parameter to balance queries and
  preserve current behavior when it is omitted.
- [x] Include journals at the exact boundary and exclude journals recorded
  afterward, comparing aware timestamps correctly across timezones.
- [x] Answer historical reads from a rebuildable derived index without replaying
  the complete journal history per query.
- [x] Update the index for in-order, out-of-order, reversal, and adjustment
  journal posts; failed posts and failed rebuilds leave existing state unchanged.
- [x] Test multiple accounts and currencies, invalid naive timestamps, and
  parity with a full journal-derived calculation.

## Planned Changes

- `src/tontine/ledger/__init__.py`
- `tests/ledger/test_ledger_posting.py`
- `tests/ledger/test_ledger_corrections.py`
- `README.md`

## Validation

```text
uv run pytest tests/ledger
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Shipped. The current balance projection is provided by TASK-STATE-005; this task
adds efficient point-in-time queries over the same immutable journal source.
