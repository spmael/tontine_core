---
id: TASK-INV-006
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-INV-001
  - FR-INV-002
  - FR-GOV-001
capability: CAP-INV-001
owner: domain
---

# Task: Automatically carry allocation rules across cycles

## Goal

Allow an approved allocation rule to be automatically reused for each eligible
contribution cycle until an explicit end condition or replacement rule applies.

## Acceptance Criteria

- [x] Define whether an allocation rule is automatically recurring or one-cycle only.
- [x] Carry a recurring rule forward to subsequent eligible cycles without duplicating or mutating the original rule.
- [x] Support an explicit end cycle, end date, cancellation, or replacement rule.
- [x] Apply replacement rules only from their effective cycle.
- [x] Preserve the allocation-rule version used by each cycle for auditability.
- [x] Reject silent changes to a rule already used by a historical cycle.
- [x] Add tests for recurring, ended, cancelled, and replaced allocation rules.

## Planned Changes

- `src/tontine/investments/`
- `src/tontine/governance/`
- `tests/investments/`
- `tests/governance/`

## Validation

```text
uv run pytest tests/investments/test_allocation_schedule.py tests/governance
uv run ruff check src/tontine/investments tests/investments
uv run mypy src/tontine/investments
```

## Completion Notes

Implemented versioned allocation-rule schedules with automatic carry-forward, bounded end cycles, cancellation, replacement at effective cycles, historical rule preservation, and optional canonical audit events.
