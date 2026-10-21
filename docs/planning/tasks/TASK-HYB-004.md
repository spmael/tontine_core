---
id: TASK-HYB-004
status: shipped
started: 2026-10-18
completed: 2026-10-18
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

- [x] Record a reversal linked to one allocation with a reason and aware timestamp.
- [x] Cancel exactly the original units, pot, and fund at the original price without repricing.
- [x] Reject a second reversal of the same allocation and a reversal of an unknown allocation.
- [x] Allow a corrected contribution to be allocated after its original is reversed.
- [x] Tests cover linkage, duplicate reversal, and derived balances after reversal.

## Planned Changes

- `src/tontine/hybrid/allocation.py`
- `src/tontine/hybrid/allocation_models.py`
- `src/tontine/hybrid/allocation_registry.py`
- `src/tontine/investments/valuation.py`
- `tests/hybrid/test_reversal.py`

## Validation

```text
uv run pytest tests/hybrid tests/investments/test_units.py -q
123 passed.

uv run ruff check src tests
All checks passed.

uv run ruff format --check src/tontine/hybrid src/tontine/investments/valuation.py tests/hybrid tests/investments/test_units.py
All files formatted.

uv run mypy src
Success: no issues found in 36 source files.

uv run pytest -q
381 passed.

uv build -o /tmp/hyb004-dist
Source distribution and wheel built successfully.

uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
72 of 72 requirements referenced; 0 uncovered; 0 undefined.

git diff --check
Passed.
```

## Completion Notes

Reversals are immutable negative offsets linked to the original allocation and
preserve its unit price. A reversal releases the cycle/member source key so a
corrected contribution can be allocated under a new contribution identifier.
See [completion evidence](../completions/TASK-HYB-004.md).
