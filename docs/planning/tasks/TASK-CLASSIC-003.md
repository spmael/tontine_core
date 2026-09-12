---
id: TASK-CLASSIC-003
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-CLS-004
capability: CAP-CLASSIC-001
owner: domain
---

# Task: Configure unpaid-contribution payout policy

## Goal

Allow a group rule to decide whether a classic payout may proceed when
contributions remain unpaid.

## Acceptance Criteria

- [x] Define an explicit allow or deny payout policy.
- [x] Require the policy when evaluating a cycle with outstanding contributions.
- [x] Reject implicit unpaid-contribution decisions.
- [x] Add tests for allowed and denied payout decisions.

## Planned Changes

- `src/tontine/classic/`
- `tests/classic/`

## Validation

```text
uv run pytest tests/classic
```

## Completion Notes

Implemented explicit allow/deny unpaid-contribution policy evaluation. A positive outstanding amount requires a policy; zero outstanding contributions remain eligible without one.
