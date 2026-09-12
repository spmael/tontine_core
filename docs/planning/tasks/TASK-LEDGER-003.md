---
id: TASK-LEDGER-003
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-LDG-003
  - FR-LDG-004
capability: CAP-LEDGER-001
owner: domain
---

# Task: Preserve posted entries and support corrections

## Goal

Keep posted journal entries immutable and make corrections traceable through
reversal or adjustment entries.

## Acceptance Criteria

- [x] Posted journal entries cannot be mutated.
- [x] Corrections create reversal or adjustment entries.
- [x] Original journal provenance remains traceable.
- [x] Duplicate journal identifiers are rejected.
- [x] Add tests for immutability, corrections, and provenance.

## Planned Changes

- `src/tontine/ledger/`
- `tests/ledger/`

## Validation

```text
uv run pytest tests/ledger
```

## Completion Notes

Implemented immutable posted journals, duplicate journal protection, traceable reversals, and explicit adjustments. Corrections preserve the original journal identifier in their source event and reference fields.
