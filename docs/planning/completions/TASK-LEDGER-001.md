---
task: TASK-LEDGER-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-LEDGER-001

## Outcome

Implemented immutable ledger vocabulary and timezone-aware journal provenance using Decimal amounts and explicit ISO 4217 currencies.

## Acceptance Criteria Evidence

- [x] Logical ledger account identifiers are validated by `LedgerAccountId`.
- [x] Debit and credit entries use Decimal amounts and explicit `CurrencyCode` values.
- [x] Journal provenance includes identifier, timezone-aware timestamp, description, source event, optional reference, and actor.
- [x] Invalid, negative, non-finite, and binary-float amounts are rejected.
- [x] Focused tests cover JPY, XAF, fractional EUR, precision, and provenance.

## Validation

```text
uv run pytest tests/ledger/test_ledger_vocabulary.py && uv run ruff check src/tontine/ledger tests/ledger/test_ledger_vocabulary.py && uv run mypy src/tontine/ledger
```

Result: 6 tests passed; Ruff and mypy passed.

## Files Changed

- `src/tontine/ledger/__init__.py`
- `tests/ledger/test_ledger_vocabulary.py`
- `docs/planning/tasks/TASK-LEDGER-001.md`

## Gaps and Follow-up

Balanced posting and balance derivation are implemented by TASK-LEDGER-002.
