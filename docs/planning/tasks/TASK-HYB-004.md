---
id: TASK-HYB-004
status: ready
started: null
completed: null
adr_refs:
  - ADR-006
requirements:
  - FR-HYB-002
capability: CAP-HYB-001
owner: domain
---

# Task: Reverse an allocation with an offsetting event

## Goal

Correct an allocation with a linked, append-only reversal that cancels its units and amounts.

## Context

ADR-006: corrections are new offsetting events; originals are never edited. Depends on TASK-HYB-003.

## Acceptance Criteria

- [ ] Record a reversal linked to one allocation with a reason and aware timestamp.
- [ ] Cancel exactly the original units, pot, and fund at the original price without repricing.
- [ ] Reject a second reversal of the same allocation and a reversal of an unknown allocation.
- [ ] Allow a corrected contribution to be allocated after its original is reversed.
- [ ] Tests cover linkage, duplicate reversal, and derived balances after reversal.

## Planned Changes

- `src/tontine/hybrid/allocation.py`
- `tests/hybrid/test_reversal.py`

## Validation

```text
uv run pytest tests/hybrid
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Not started.
