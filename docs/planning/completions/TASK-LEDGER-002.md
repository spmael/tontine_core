---
task: TASK-LEDGER-002
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-LEDGER-002

## Outcome

Implemented balanced double-entry journal posting and derived account balances from immutable posted entries.

## Acceptance Criteria Evidence

- [x] Journals require at least one debit and one credit entry.
- [x] Unbalanced debit and credit totals are rejected.
- [x] Account balances are derived by aggregating posted entries.
- [x] Monetary calculations use Decimal arithmetic.
- [x] Tests cover balanced, unbalanced, missing-direction, and derived-balance scenarios.

## Validation

```text
uv run pytest tests/ledger/test_ledger_posting.py && uv run ruff check src/tontine/ledger tests/ledger && uv run mypy src/tontine/ledger
```

Result: 3 tests passed; Ruff and mypy passed.

## Files Changed

- `src/tontine/ledger/__init__.py`
- `tests/ledger/test_ledger_posting.py`
- `docs/planning/tasks/TASK-LEDGER-002.md`

## Gaps and Follow-up

Corrections and immutable-posting evidence are recorded in TASK-LEDGER-003.
