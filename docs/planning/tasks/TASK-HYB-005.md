---
id: TASK-HYB-005
status: ready
started: null
completed: null
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

- [ ] Apply a partial payment in the versioned penalty and contribution order and record the version used.
- [ ] Add a `ROTATION_POT` penalty destination without changing the existing default.
- [ ] Record an arrears event when a cycle closes with a contribution unpaid; a missed contribution issues no units.
- [ ] Record a member catch-up or forfeit election within the deadline; apply the group default at the deadline; price catch-up at the valuation in force when the member pays, or hold it as pending allocation if none is in force or it is too old.
- [ ] Forfeiting ends fund arrears for that cycle only and never rotation arrears.
- [ ] Block redemption while rotation arrears are owed and allow an explicit arrears offset against units.
- [ ] Waive a penalty only with an approved waiver decision.
- [ ] Tests cover each payment order, arrears, elections, default forfeit, collateral, and waivers.

## Planned Changes

- `src/tontine/hybrid/arrears.py`
- `src/tontine/contributions/__init__.py`
- `tests/hybrid/test_arrears.py`

## Validation

```text
uv run pytest tests/hybrid tests/contributions
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Not started.
