---
task: TASK-API-002
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-API-002

## Outcome

Added stable top-level public imports and framework-independent creation helpers for groups and contribution cycles, with representative Classic and Investment usage examples.

## Acceptance Criteria Evidence

- [x] Stable imports expose domain types without adapter dependencies.
- [x] Public helpers have concise Google-style docstrings.
- [x] `examples/public_api.py` covers group creation, cycles, Classic rotation, and investment allocation.
- [x] Authentication and access-control decisions remain outside the package boundary.
- [x] Public API tests execute representative domain calls without infrastructure.

## Validation

```text
uv run pytest tests/test_import.py tests/test_public_api.py
uv run ruff check src tests
uv run mypy src
```

Result: 3 public API tests passed; Ruff and mypy passed.

## Files Changed

- `src/tontine/__init__.py`
- `tests/test_public_api.py`
- `examples/public_api.py`
- `README.md`
- `docs/planning/tasks/TASK-API-002.md`

## Gaps and Follow-up

Database and framework adapters remain outside the core package as documented by TASK-API-001.