---
task: TASK-LEDGER-004
started: 2026-10-21
completed: 2026-10-21
status: shipped
---

# Completion: Add indexed point-in-time ledger balances

## Outcome

`InMemoryLedgerRepository.balance_for` accepts an optional timezone-aware
`as_of` timestamp. Per-account/currency cumulative histories are indexed by
recorded time and binary-searched for historical reads. New journals, including
out-of-order posts, reversals, and adjustments, update both current and
historical derived projections. Rebuild validates and reconstructs both
projections from immutable journals before replacing existing derived state.

## Acceptance Criteria Evidence

- [x] Optional `as_of` preserves existing current-balance behavior and rejects
  naive timestamps.
- [x] Historical reads include the exact timestamp boundary and compare
  equivalent aware instants across timezones and daylight-saving folds.
- [x] Historical balance reads query a cumulative per-account/currency index
  without replaying journal history.
- [x] Out-of-order and same-time posts, reversals, adjustments, and rebuilds
  preserve equality with full journal-derived calculations.
- [x] Tests cover multiple accounts and currencies, invalid journals and
  timestamps, and failed rebuild atomicity.

## Validation

```text
uv run pytest
454 passed.

uv run ruff check src tests
All checks passed.

uv run ruff format --check src/tontine/ledger/__init__.py tests/ledger
4 changed Python files already formatted.

uv run mypy src
Success: no issues found in 46 source files.

uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
72 requirements referenced; 0 uncovered; 0 undefined.
```

## Files Changed

- `README.md`
- `docs/planning/capabilities/CAP-LEDGER-002.md`
- `docs/planning/completions/TASK-LEDGER-004.md`
- `docs/planning/tasks/TASK-LEDGER-004.md`
- `src/tontine/ledger/__init__.py`
- `tests/ledger/test_ledger_corrections.py`
- `tests/ledger/test_ledger_posting.py`

## Gaps and Follow-up

- Journal timestamps define historical recognition: later reversals and
  adjustments affect balances from their own `recorded_at` instant onward.
