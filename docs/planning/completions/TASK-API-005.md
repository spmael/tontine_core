---
task: TASK-API-005
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-API-005

## Outcome

Governance and allocation schedule mutations accept optional, timezone-aware
occurrence timestamps. Explicit values are preserved in audit events, including
both proposal evaluation and approval events. Omitted values continue to use
the current local time.

## Acceptance Criteria Evidence

- [x] Governance vote, evaluation, and ruleset creation accept optional
  `occurred_at` values; allocation rule addition and cancellation accept the
  same parameter.
- [x] Evaluation uses one supplied instant for both its evaluation and approval
  events.
- [x] Naive timestamps raise the actionable `occurred_at` validation error
  before any corresponding state change.
- [x] Tests verify exact timestamp preservation, naive-input rejection, and
  timezone-aware defaults when `occurred_at` is omitted.
- [x] Public method docstrings document the optional parameters, timezone
  requirements, and default behavior.

## Validation

```text
uv run pytest tests/governance tests/investments/test_allocation_schedule.py tests/audit
uv run ruff check src tests
uv run mypy src
git diff --check
```

Result: 19 focused tests passed; Ruff, mypy, and whitespace checks passed.

## Files Changed

- `src/tontine/governance/__init__.py`
- `src/tontine/investments/__init__.py`
- `tests/governance/test_governance.py`
- `tests/investments/test_allocation_schedule.py`
- `docs/planning/tasks/TASK-API-005.md`
- `docs/planning/capabilities/CAP-API-002.md`
- `docs/planning/completions/TASK-API-005.md`

## Gaps and Follow-up

- `CAP-API-002` remains partial because its unrelated documented-domain-error
  and framework-independence acceptance criteria are not complete.
