---
id: TASK-HYB-003
status: ready
started: null
completed: null
adr_refs:
  - ADR-006
requirements:
  - FR-HYB-002
  - FR-HYB-003
capability: CAP-HYB-001
owner: domain
---

# Task: Issue units from a recorded contribution once

## Goal

Record an allocation event that issues investment units from a recorded contribution at a stored valuation.

## Context

ADR-006 invariants and pricing. Depends on TASK-HYB-002.

## Acceptance Criteria

- [ ] Create an allocation only from a recorded contribution; reject a second allocation for the same `contribution_id`.
- [ ] Store contribution, member, cycle, rule version, payment-order version, valuation reference, unit price, pot, fund, units, and cash residual.
- [ ] Price at the latest valuation in force on the receipt date; use the launch price while no units are outstanding.
- [ ] Hold the fund share as pending allocation when no valuation is in force or it exceeds the maximum age, then allocate at the next valuation without backdating.
- [ ] Round units down to 4 decimal places and keep the residual as fund cash.
- [ ] Issue member units through `MemberUnitLedger` with the allocation as provenance.
- [ ] Tests cover duplicates, pending allocation, launch price, stale valuations, rounding, and replay without re-resolution.

## Planned Changes

- `src/tontine/hybrid/allocation.py`
- `tests/hybrid/test_allocation.py`

## Validation

```text
uv run pytest tests/hybrid
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Not started.
