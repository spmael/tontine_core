---
task: TASK-INV-004
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-INV-004

## Outcome

Implemented deterministic Decimal member-unit issuance and redemption with
operation-maintained balances and duplicate event protection.

## Acceptance Criteria Evidence

- [x] Unit issuance derives units from an explicit contribution amount and positive unit price.
- [x] Invalid unit quantities are rejected through Decimal validation and balance checks.
- [x] Member balances are maintained through issue and redemption operations.
- [x] Unit distributions are not modeled; redemption is the supported balance-reduction path.
- [x] Focused tests cover late joining, additional contributions, redemptions, and member exit.

## Validation

```text
uv run pytest tests/investments/test_units.py
```

Result: 4 tests passed.

## Files Changed

- `src/tontine/investments/__init__.py`
- `tests/investments/test_units.py`
- `docs/planning/tasks/TASK-INV-004.md`

## Gaps and Follow-up

The unit ledger does not retain replayable unit-event records in the current baseline.
