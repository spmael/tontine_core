---
task: TASK-CON-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-CON-001

## Outcome

Implemented contribution rule and cycle vocabulary for daily, weekly, and monthly contribution schedules with explicit IANA timezone handling.

## Acceptance Criteria Evidence

- [x] Contribution amounts use `decimal.Decimal`: `ContributionRule` and `ContributionCycle` normalize and validate monetary amounts with Decimal arithmetic.
- [x] Rules require amount, currency, frequency, due-date convention, grace period, effective date, and timezone: `ContributionRule` validates all fields and supports `daily`, `weekly`, and `monthly` choices.
- [x] Cycles have explicit status and due date: `ContributionCycle` exposes `CycleStatus`, `start_date`, and `due_date`.
- [x] Invalid or negative amounts are rejected: amount normalization rejects invalid, non-finite, and negative values.
- [x] Unit tests cover JPY 30,000 daily, monthly, and weekly rules: `tests/contributions/test_contribution_rules.py`.
- [x] Timezone behavior is explicit: IANA timezone names are validated, and payment timestamps must be timezone-aware before local-date classification.

## Validation

```text
uv run pytest tests/contributions/test_contribution_rules.py && uv run ruff check src/tontine/contributions/__init__.py src/tontine/exceptions.py && uv run mypy src/tontine/contributions src/tontine/exceptions.py
```

Result: 6 tests passed; Ruff and mypy passed.

## Files Changed

- `docs/planning/requirements.md`
- `docs/planning/capabilities/CAP-CON-001.md`
- `docs/planning/tasks/TASK-CON-001.md`
- `src/tontine/contributions/__init__.py`
- `src/tontine/exceptions.py`
- `tests/contributions/test_contribution_rules.py`

## Gaps and Follow-up

Contribution recording classification, duplicate adjustment behavior, and outstanding-contribution reporting require the remaining CAP-CON-001 tasks.
