---
task: TASK-STATE-001
started: 2026-10-18
completed: 2026-10-18
status: shipped
---

# Completion: Snapshot and rebuild member unit state

## Outcome

Added frozen issue and redemption event values and a schema-v1
`MemberUnitLedgerSnapshot`. The snapshot stores the ordered event history rather
than balances and validates duplicate identifiers and redemptions against the
balance at each event position. `MemberUnitLedger.from_snapshot` rebuilds the
derived projection. Existing priced and pre-priced issuance methods remain
available, and invalid operations no longer reserve an event identifier.

## Acceptance Criteria Evidence

- [x] Unit issue and redemption are recorded in an immutable ordered event
  stream with unique non-empty identifiers.
- [x] The schema-v1 snapshot contains events, not balances, and deterministically
  restores the ledger.
- [x] Unsupported schemas, duplicate IDs, and overdrawn redemption sequences
  are rejected.
- [x] Failed issue and redemption operations leave the event stream and balances
  unchanged and allow a valid retry with the same event ID.
- [x] Existing hybrid callers and unit calculations retain their behavior;
  snapshot and event types are imported from `tontine.investments`.
- [x] README and ADR-007 document the event-only snapshot and its role in hybrid
  state restoration.

## Validation

```text
uv run pytest tests/investments/test_units.py tests/hybrid
158 passed.

uv run ruff check src/tontine/investments/valuation.py src/tontine/investments/__init__.py tests/investments/test_units.py
All checks passed.

uv run ruff format --check src/tontine/investments/valuation.py src/tontine/investments/__init__.py tests/investments/test_units.py
All three files already formatted.

uv run mypy src/tontine/investments
Success: no issues found in 7 source files.

Pylance syntax checks for valuation.py and test_units.py
No syntax errors found.

Pylance textDocument/diagnostic for valuation.py
No diagnostics.
```

## Files Changed

- `README.md`
- `docs/architecture/adr/ADR-007-state-interchange-contract.md`
- `docs/planning/capabilities/CAP-STATE-001.md`
- `docs/planning/completions/TASK-STATE-001.md`
- `docs/planning/tasks/TASK-STATE-001.md`
- `src/tontine/investments/__init__.py`
- `src/tontine/investments/valuation.py`
- `tests/investments/test_units.py`

## Gaps and Follow-up

- Hybrid allocation, arrears, and exit registry snapshots remain in
  TASK-STATE-002 through TASK-STATE-004.
- Rebuildable ledger balance projections remain in TASK-STATE-005.
