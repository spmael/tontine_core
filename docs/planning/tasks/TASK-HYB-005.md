---
id: TASK-HYB-005
status: shipped
started: 2026-10-18
completed: 2026-10-18
adr_refs:
  - ADR-006
requirements:
  - FR-HYB-003
capability: CAP-HYB-001
owner: domain
---

# Task: Apply partial payments, arrears, catch-up, and collateral

## Goal

Make late, missed, partial, and catch-up outcomes explicit events.

## Context

ADR-006 partial payments, missed contributions, and collateral. Depends on TASK-HYB-003 and TASK-GOV-007.

## Acceptance Criteria

- [x] Apply a partial payment in the versioned penalty and contribution order and record the version used.
- [x] Add a `ROTATION_POT` penalty destination without changing the existing default.
- [x] Record an arrears event when a cycle closes with a contribution unpaid; a missed contribution issues no units.
- [x] Record a member catch-up or forfeit election within the deadline; apply the group default when that cycle closes; price catch-up at the valuation in force when the member pays, or hold it as pending allocation if none is in force or it is too old.
- [x] Forfeiting ends fund arrears for that cycle only and never rotation arrears.
- [x] Block redemption while rotation arrears are owed and allow an explicit arrears offset against units.
- [x] Waive a penalty only with an approved waiver decision.
- [x] Tests cover each payment order, arrears, elections, default forfeit, collateral, and waivers.

## Planned Changes

- `src/tontine/hybrid/arrears.py`
- `src/tontine/hybrid/__init__.py`
- `src/tontine/hybrid/allocation.py`
- `src/tontine/hybrid/allocation_models.py`
- `src/tontine/hybrid/allocation_registry.py`
- `src/tontine/contributions/__init__.py`
- `tests/hybrid/test_arrears.py`

## Validation

```text
uv run pytest tests/hybrid tests/contributions
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Cycle-close arrears, versioned payment application, catch-up elections and
deadline outcomes, receipt-date unit allocation, governance-linked penalty
waivers, redemption gating, and explicit unit offsets are implemented. Catch-up
allocations use the existing reversal registry and retain their arrears source.
Cycle and arrears events are recorded in the shared audit registry. Payment
application records an already received amount; the library does not initiate
payments or move funds.
