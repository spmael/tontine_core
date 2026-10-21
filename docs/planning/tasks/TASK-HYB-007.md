---
id: TASK-HYB-007
status: shipped
started: 2026-10-18
completed: 2026-10-18
adr_refs:
  - ADR-006
requirements:
  - FR-HYB-004
  - FR-HYB-005
capability: CAP-HYB-001
owner: domain
---

# Task: Report the combined settlement position

## Goal

Derive a member's dues, rotation position, and units in one pure settlement view and statement.

## Context

ADR-006: `settlement_position(history, member, valuation)` is pure and never stored. Depends on TASK-HYB-006.

## Acceptance Criteria

- [x] Derive outstanding dues, penalties, rotation pot received versus paid in, units, and unit value from recorded events only.
- [x] Show pending allocations, pending exits, elections, and offsets as explicit lines.
- [x] Present units as "member funds: redeemable" with a liability flag by default, derived from the statute flags; keep the pot position separate and ranked ahead of units. Store no classification in the domain.
- [x] Extend member reporting with the hybrid position from the same event lineage.
- [x] Integration test runs contributions through allocation, arrears, and exit to the member report.
- [x] Update the BRD current-baseline section and README with shipped behavior.

## Planned Changes

- `src/tontine/hybrid/settlement.py`
- `src/tontine/hybrid/settlement_history.py`
- `src/tontine/reporting/`
- `tests/hybrid/test_settlement.py`

## Validation

```text
uv run pytest
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Implemented the immutable settlement-history snapshot and pure position
projection, extended member statements, and documented the combined reporting
behavior. See `docs/planning/completions/TASK-HYB-007.md` for verification.
