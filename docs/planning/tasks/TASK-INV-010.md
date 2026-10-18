---
id: TASK-INV-010
status: shipped
started: 2026-10-19
completed: 2026-10-19
requirements:
  - FR-INV-008
capability: CAP-INV-002
owner: domain
---

# Task: Apply the zero-amount activity policy

## Goal

Accept zero amounts only for activity types where they are meaningful. Review
found none, so purchase, sale, income, and fee amounts must be positive.

## Acceptance Criteria

- [x] Record the reviewed zero-amount policy per activity type in ADR-005,
  including the meaning of `amount`, gross recording, unit-only events, and the
  reversal and waiver follow-ups.
- [x] Drive the rule from one per-type `{type: allow zero}` table.
- [x] Reject amounts below the currency's smallest ISO 4217 unit instead of
  rounding, including the converted asset-currency amount.
- [x] Make the rejection message name the note, reversal, or corporate-action
  path.
- [x] Require strictly positive `units` on purchases and sales from a per-type
  table, and reject units on income and fees.
- [x] Test `0`, `0.00`, `-0`, `0E-10`, negative, NaN, and Infinity amounts;
  0.001 XAF and EUR; the smallest valid amount per currency; and a converted
  amount below the asset unit.

## Planned Changes

- `docs/architecture/adr/ADR-005-investment-activity-and-valuation-policy.md`
- `src/tontine/investments/activity.py`
- `src/tontine/currencies/__init__.py`
- `tests/investments/`, `tests/currencies/`, `tests/governance/`

## Validation

```text
uv run pytest tests/investments
```

## Completion Notes

Decided by auditor, investment operations, compliance, and ledger architecture
review. Purchases and sales now carry strictly positive asset `units`. See the
[completion record](../completions/TASK-INV-010.md).
