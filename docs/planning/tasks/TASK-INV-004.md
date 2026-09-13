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

Track deterministic member-unit issuance and redemption with derived balances.

## Acceptance Criteria

- [x] Issue units from an explicit contribution and unit price.
- [x] Reject negative or non-finite unit quantities.
- [x] Track member unit balances through issue and redemption operations.
- [x] Support redemption deterministically without unit distributions.
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
