---
id: TASK-INV-008
status: shipped
started: 2026-10-18
completed: 2026-10-18
requirements:
  - FR-INV-007
  - FR-INV-008
capability: CAP-INV-002
owner: domain
---

# Task: Validate activity currency and query recorded activity

## Goal

Validate activity currency against its asset with explicit FX conversion inputs
per ADR-005, and provide deterministic activity queries.

## Acceptance Criteria

- [x] Accept same-currency activity without an FX rate and reject a redundant one.
- [x] Require an FX rate for exactly the activity and asset currency pair for
  cross-currency activity, accepting either quotation direction.
- [x] Retain the original amount and currency, the rate with its source, and the
  unquantized asset-currency amount.
- [x] Reject activity whose asset conflicts with a previously recorded definition.
- [x] Query activity by asset, type, and inclusive effective-date bounds in
  effective-date, recorded-time, and event-ID order.
- [x] Add tests for conversion, pair mismatch, direction, and query ordering.

## Planned Changes

- `src/tontine/investments/activity.py`
- `src/tontine/investments/fx.py`
- `tests/investments/test_activity_validation.py`
- `tests/investments/test_fx_boundary.py`

## Validation

```text
uv run pytest tests/investments
uv run mypy src
```

## Completion Notes

See [completion record](../completions/TASK-INV-008.md). Zero-amount policy is
tracked separately in TASK-INV-010.
