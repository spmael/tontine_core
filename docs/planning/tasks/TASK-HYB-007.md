---
id: TASK-HYB-007
status: ready
started: null
completed: null
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

- [ ] Derive outstanding dues, penalties, rotation pot received versus paid in, units, and unit value from recorded events only.
- [ ] Show pending allocations, pending exits, elections, and offsets as explicit lines.
- [ ] Present units as "member funds: redeemable" with a liability flag by default, derived from the statute flags; keep the pot position separate and ranked ahead of units. Store no classification in the domain.
- [ ] Extend member reporting with the hybrid position from the same event lineage.
- [ ] Integration test runs contributions through allocation, arrears, and exit to the member report.
- [ ] Update the BRD current-baseline section and README with shipped behavior.

## Planned Changes

- `src/tontine/hybrid/settlement.py`
- `src/tontine/reporting/`
- `tests/hybrid/test_settlement.py`

## Validation

```text
uv run pytest
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Not started.
