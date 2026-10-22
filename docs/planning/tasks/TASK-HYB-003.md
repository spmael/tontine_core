---
id: TASK-HYB-003
status: shipped
started: 2026-10-18
completed: 2026-10-18
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

- [x] Create an allocation only from a recorded contribution; reject a second allocation for the same `contribution_id`.
- [x] Store contribution, member, cycle, rule version, payment-order version, valuation reference, unit price, pot, fund, units, and cash residual.
- [x] Price at the latest valuation in force on the receipt date; use the launch price while no units are outstanding.
- [x] Hold the fund share as pending allocation when no valuation is in force or it exceeds the maximum age, then allocate at the next valuation without backdating.
- [x] Round units down to 4 decimal places and keep the residual as fund cash.
- [x] Issue member units through `MemberUnitLedger` with the allocation as provenance.
- [x] Tests cover duplicates, pending allocation, launch price, stale valuations, rounding, and replay without re-resolution.

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

Implemented and verified on 2026-10-18; see
[completion evidence](../completions/TASK-HYB-003.md). A contribution's stable
identifier is supplied by the caller, and the cycle/member source key is also
enforced to prevent allocating that recorded contribution under another ID.
The launch price is used when the unit ledger has no outstanding units;
otherwise an absent or stale valuation leaves the fund share pending.
