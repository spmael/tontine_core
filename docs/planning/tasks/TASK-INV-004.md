---
id: TASK-INV-004
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-INV-004
capability: CAP-INV-001
owner: domain
---

# Task: Implement deterministic member units

## Goal

Track member units and deterministic issuance, redemption, contribution, and
distribution effects.

## Acceptance Criteria

- [x] Issue units from an explicit contribution and unit price.
- [x] Reject negative or non-finite unit quantities.
- [x] Track member unit balances from immutable unit events.
- [x] Support redemption and distribution events deterministically.
- [x] Add tests for missed contributions, late joining, additional contributions, and member exit.

## Planned Changes

- `src/tontine/investments/`
- `tests/investments/`

## Validation

```text
uv run pytest tests/investments/test_units.py
```

## Completion Notes

Implemented deterministic member unit issuance and redemption with derived balances and duplicate event protection. Contribution timing policies remain inputs from the contribution capability.
