---
task: TASK-STATE-005
started: 2026-10-21
completed: 2026-10-21
status: shipped
---

# Completion: Rebuildable ledger balance projection

## Outcome

`InMemoryLedgerRepository` now maintains current balances keyed by ledger
account and currency as balanced journals are posted. Balance queries read the
derived projection rather than scanning journal history. The repository exposes
posted journals as an immutable tuple and can validate and rebuild its
projection deterministically from that journal sequence.

## Acceptance Criteria Evidence

- [x] Successful posts update the derived account/currency balances; failed
  posts leave journal history and balances unchanged.
- [x] Rebuild validates every journal, detects duplicate identifiers, and
  replaces the projection only after a successful complete replay.
- [x] Journal records are frozen, history is returned as a tuple, and no
  public operation sets a cached balance.
- [x] Full journal-derived calculations match projection values after posts,
  reversals, adjustments, and projection rebuild.
- [x] Tests cover multiple accounts and currencies, invalid journals,
  duplicate posts, reversal and adjustment behavior.

## Validation

```text
uv run pytest
450 passed.

uv run ruff check src tests
All checks passed.

uv run ruff format --check src/tontine/ledger/__init__.py tests/ledger/test_ledger_posting.py tests/ledger/test_ledger_corrections.py
3 changed files already formatted.

uv run mypy src
Success: no issues found in 46 source files.

uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
72 requirements referenced; 0 uncovered; 0 undefined.
```

The repository-wide `ruff format --check src tests` also reports existing
formatting drift in seven unrelated files; those files were not changed.

## Files Changed

- `README.md`
- `docs/planning/capabilities/CAP-STATE-001.md`
- `docs/planning/completions/TASK-STATE-005.md`
- `docs/planning/tasks/TASK-STATE-005.md`
- `src/tontine/ledger/__init__.py`
- `tests/ledger/test_ledger_corrections.py`
- `tests/ledger/test_ledger_posting.py`

## Gaps and Follow-up

- Point-in-time ledger balance queries remain in CAP-LEDGER-002.
