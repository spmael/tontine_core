---
task: TASK-API-004
status: shipped
started: 2026-10-12
completed: 2026-10-12
---

# Completion: TASK-API-004

## Outcome

Standardized timezone-awareness validation for public datetime inputs. Errors
identify the field or parameter and explain how to construct an aware value
using `datetime.timezone.utc` or `zoneinfo.ZoneInfo`. Naive timestamps remain
rejected without being assigned an implicit timezone.

## Acceptance Criteria Evidence

- [x] Identify the exact invalid input: shared validator used for contribution
  `payment_date`/`as_of`, `Penalty.assessed_on`, payout and journal
  `recorded_at`, audit `occurred_at`, investment activity `recorded_at`, FX
  `effective_at`/`as_of`, and governance `created_at`/`voting_deadline`.
- [x] Provide explicit `datetime.timezone.utc` and `zoneinfo.ZoneInfo`
  construction guidance in each validation error and relevant public docstrings.
- [x] Keep naive datetime rejection and aware datetime semantics; existing
  timezone conversion and freshness tests continue to pass.
- [x] Add regression coverage for all affected fields, including both naive and
  aware inputs and actionable error text.
- [x] Document timezone requirements on the affected public records and APIs.

## Validation

```text
uv run pytest tests/contributions tests/classic tests/ledger tests/investments tests/governance tests/audit
uv run pytest
uv run ruff check src tests
uv run mypy src
git diff --check
```

Result: focused suites passed (73 tests); full suite passed (123 tests); Ruff,
mypy, and diff checks passed.

## Files Changed

- `src/tontine/_datetime.py`
- `src/tontine/contributions/__init__.py`
- `src/tontine/classic/__init__.py`
- `src/tontine/ledger/__init__.py`
- `src/tontine/investments/__init__.py`
- `src/tontine/governance/__init__.py`
- `src/tontine/audit/__init__.py`
- `tests/contributions/`
- `tests/classic/`
- `tests/ledger/`
- `tests/investments/`
- `tests/governance/`
- `tests/audit/`
- `docs/planning/tasks/TASK-API-004.md`
- `docs/planning/capabilities/CAP-API-002.md`

## Gaps and Follow-up

- TASK-API-005 remains responsible for caller-supplied occurrence times on
  governance and investment-allocation mutations.
