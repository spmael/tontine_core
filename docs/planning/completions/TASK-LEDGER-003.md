---
task: TASK-LEDGER-003
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-LEDGER-003

## Outcome

Implemented immutable posted journals, duplicate journal protection, reversals, adjustments, and provenance traceability.

## Acceptance Criteria Evidence

- [x] Posted journal entries cannot be mutated: `JournalEntry` and `LedgerEntry` are frozen dataclasses.
- [x] Corrections create reversal or adjustment entries: `LedgerRepository.reverse()` and `adjust()` post new journals.
- [x] Original journal provenance remains traceable: correction source events and references retain the original journal identifier.
- [x] Duplicate journal identifiers are rejected through `DuplicateJournalError`.
- [x] Tests cover immutability, duplicate IDs, reversals, adjustments, and derived balance effects.

## Validation

```text
uv run pytest tests/ledger && uv run ruff check src/tontine/ledger tests/ledger && uv run mypy src/tontine/ledger
```

Result: 13 tests passed; Ruff and mypy passed.

## Files Changed

- `src/tontine/exceptions.py`
- `src/tontine/ledger/__init__.py`
- `tests/ledger/test_ledger_corrections.py`
- `docs/architecture/adr/ADR-001-ledger-precision-and-rounding.md`
- `docs/architecture/ledger-contract.md`
- `docs/planning/tasks/TASK-LEDGER-003.md`

## Gaps and Follow-up

Future rounding-policy value objects remain outside the V1 ledger capability and should be planned when interest, FX, tax, or unit calculations are introduced.
