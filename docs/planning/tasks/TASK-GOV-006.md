---
id: TASK-GOV-006
status: shipped
started: 2026-10-18
completed: 2026-10-18
requirements:
  - FR-INV-009
capability: CAP-INV-002
owner: domain
---

# Task: Add a typed investment authorization effect

## Goal

Let governance proposals authorize a purchase or sale of one asset up to a
cumulative maximum in the asset currency, per ADR-005.

## Acceptance Criteria

- [x] Add `InvestmentAuthorizationEffect` limited to purchases and sales with a
  positive Decimal maximum and explicit currency.
- [x] Create investment authorization proposals without rotation fields.
- [x] Audit approval with `investment_authorization_approved`.
- [x] Expose `approved_investment_authorization` that rejects unknown,
  unapproved, and non-investment proposals.
- [x] Preserve the effect through governance snapshots and validate its
  approval provenance.
- [x] Add tests for the effect, lookup, audit event, and snapshot round trip.

## Planned Changes

- `src/tontine/governance/`
- `tests/governance/test_investment_authorization.py`

## Validation

```text
uv run pytest tests/governance
uv run mypy src
```

## Completion Notes

See [completion record](../completions/TASK-GOV-006.md).
