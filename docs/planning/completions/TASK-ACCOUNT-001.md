---
task: TASK-ACCOUNT-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-ACCOUNT-001

## Outcome

Implemented immutable financial account records for external custody locations without storing credentials or enabling external access.

## Acceptance Criteria Evidence

- [x] Supports cash, bank, microfinance, mobile wallet, broker, and other account types through `AccountType`.
- [x] Requires explicit currency and institutional metadata for bank, microfinance, mobile-wallet, and broker accounts.
- [x] Stores only masked account references.
- [x] Rejects credential-like values, long unmasked digit sequences, and references without a mask marker.
- [x] Includes concise public docstrings and invariant-focused tests.

## Validation

```text
uv run pytest tests/accounts/test_account_records.py && uv run ruff check src/tontine/accounts/__init__.py tests/accounts/test_account_records.py && uv run mypy src/tontine/accounts
```

Result: 4 tests passed; Ruff and mypy passed.

## Files Changed

- `src/tontine/accounts/__init__.py`
- `src/tontine/exceptions.py`
- `tests/accounts/test_account_records.py`
- `docs/planning/tasks/TASK-ACCOUNT-001.md`

## Gaps and Follow-up

Account registry event references are handled by TASK-ACCOUNT-002.
