---
task: TASK-GOV-006
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-GOV-006

## Outcome

Governance supports `InvestmentAuthorizationEffect` proposals, audits their
approval, exposes `approved_investment_authorization`, and preserves the effect
through snapshots with approval-provenance validation. Snapshot schema version 1
is unchanged because snapshots hold typed effect objects.

## Acceptance Criteria Evidence

- [x] Effect validation: `test_effect_accepts_only_positive_purchase_or_sale_limits`.
- [x] Audit and snapshot: `test_approved_authorization_is_audited_and_survives_snapshot`.
- [x] Lookup rejections: `test_lookup_rejects_unknown_unapproved_or_non_investment_proposals`.

All in `tests/governance/test_investment_authorization.py`.

## Validation

```text
uv run pytest
189 passed
uv run ruff check src tests
uv run mypy src
```

## Changed Files

- `src/tontine/governance/_investment_authorization.py`, `models.py`,
  `registry.py`, `snapshots.py`, `snapshot_validation.py`, `__init__.py`

## Remaining Gaps

`registry.py` is 563 lines, slightly above the size guideline it already
exceeded; new methods were placed in a separate mixin module.
