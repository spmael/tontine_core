---
id: TASK-INV-009
status: shipped
started: 2026-10-18
completed: 2026-10-18
requirements:
  - FR-INV-009
capability: CAP-INV-002
owner: domain
---

# Task: Link purchases and sales to authorizing decisions

## Goal

Retain a structured decision reference on purchases and sales and validate it
through an optional governance lookup, per ADR-005.

## Acceptance Criteria

- [x] Add `DecisionReference` and accept it only on purchases and sales.
- [x] Validate references through an `InvestmentAuthorizationLookup` supplied to
  the activity registry, without importing governance at runtime.
- [x] Require the decision's asset, activity type, and currency to match.
- [x] Enforce the decision maximum cumulatively in asset-currency amounts.
- [x] Reject references when no lookup is configured.
- [x] Add tests for matching, cumulative limits, cross-currency totals, and
  rejected decisions.

## Planned Changes

- `src/tontine/investments/activity.py`
- `tests/governance/test_investment_authorization.py`

## Validation

```text
uv run pytest tests/governance/test_investment_authorization.py
uv run mypy src
```

## Completion Notes

See [completion record](../completions/TASK-INV-009.md).
