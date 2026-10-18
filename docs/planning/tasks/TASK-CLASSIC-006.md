---
id: TASK-CLASSIC-006
status: shipped
started: 2026-10-18
completed: 2026-10-18
requirements:
  - FR-CLS-005
  - FR-GOV-010
capability: CAP-CLASSIC-002
owner: domain
---

# Task: Apply approved one-cycle recipient overrides

## Goal

Resolve a separately approved recipient override for exactly one cycle without
changing the base rotation or payout rules.

## Context

An exception replaces only that cycle's recipient. Its recipient must belong to
the rotation effective for that cycle. Payout amount and unpaid-contribution
eligibility continue to follow the existing classic rules.

## Acceptance Criteria

- [x] Represent approval provenance with an immutable exception value carrying
  its cycle, recipient, proposal reference, approval event reference, and
  timezone-aware approval time.
- [x] Apply at most one approved exception to a cycle and reject invalid cycle
  scope or recipients.
- [x] Expose the selected recipient while retaining the effective base rotation
  for payout calculation.
- [x] Leave the base schedule, adjacent-cycle recipients, payout amount, and
  unpaid-contribution policy unchanged.
- [x] Test exception scope, immutability, invalid inputs, and recipient
  restoration through the public classic API.

## Planned Changes

- `src/tontine/classic/`
- `tests/classic/test_rotation_schedule.py`

## Validation

```text
uv run pytest tests/classic tests/governance
uv run ruff check src/tontine/classic tests/classic
uv run mypy src/tontine/classic src/tontine/governance
```

## Completion Notes

Governance proposal creation and approval remain in `CAP-GOV-002`; this classic
schedule consumes an explicit approved-effect value and does not replay votes.
See `docs/planning/completions/TASK-CLASSIC-006.md`.
