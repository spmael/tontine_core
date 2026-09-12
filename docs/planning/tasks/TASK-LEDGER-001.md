---
id: TASK-LEDGER-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-LDG-001
  - FR-LDG-003
  - NFR-CAL-001
  - NFR-CAL-002
capability: CAP-LEDGER-001
owner: domain
---

# Task: Define ledger vocabulary and journal provenance

## Goal

Define immutable, Decimal-based ledger values and journal provenance without
posting or integrating with external systems.

## Acceptance Criteria

- [x] Define logical ledger account identifiers.
- [x] Define Decimal-based debit and credit entries with explicit ISO currency.
- [x] Define journal provenance with identifier, timestamps, description, source event, reference, and actor.
- [x] Reject invalid, negative, non-finite, and binary-float monetary values.
- [x] Add focused vocabulary and precision tests.

## Planned Changes

- `src/tontine/ledger/`
- `tests/ledger/`

## Validation

```text
uv run pytest tests/ledger/test_ledger_vocabulary.py
```

## Completion Notes

Implemented immutable ledger account IDs, Decimal debit and credit entries, ISO currency validation, and timezone-aware journal provenance. Posting and balance derivation remain in the next task.
