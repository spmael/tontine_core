---
id: TASK-CLASSIC-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-CLS-001
  - FR-CLS-002
capability: CAP-CLASSIC-001
owner: domain
---

# Task: Define classic rotation and recipient selection

## Goal

Define a deterministic classic tontine rotation and calculate each cycle's
expected payout from Decimal contribution amounts.

## Acceptance Criteria

- [x] Rotation order contains unique active member identifiers.
- [x] Missing or duplicate active members are rejected.
- [x] Cycle recipient selection is deterministic and wraps around the order.
- [x] Expected payout is the Decimal sum of cycle contributions.
- [x] Tests cover the JPY 30,000 five-member example.

## Planned Changes

- `src/tontine/classic/`
- `tests/classic/`

## Validation

```text
uv run pytest tests/classic/test_rotation.py
```

## Completion Notes

Implemented deterministic classic rotation order, one-based cycle recipient selection with wraparound, and Decimal expected-payout calculation for active members.
