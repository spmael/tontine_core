---
task: TASK-PACKAGE-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-PACKAGE-001

## Outcome

Created the `src/tontine` import package with public version metadata, domain
exceptions, and initial group and member package boundaries.

## Acceptance Criteria Evidence

- [x] `src/tontine/__init__.py` imports successfully: `uv run python -c "import tontine"`.
- [x] Initial capability directories exist: `src/tontine/groups/` and `src/tontine/members/`.
- [x] The public import name is `tontine`: smoke test imports `tontine`.
- [x] No framework or persistence dependency enters the core package: package files use only the standard library.

## Validation

```text
uv run python -c "import tontine"
uv run pytest tests/test_import.py
```

Both checks passed.

## Files Changed

- `src/tontine/__init__.py`
- `src/tontine/exceptions.py`
- `src/tontine/groups/__init__.py`
- `src/tontine/members/__init__.py`
- `tests/test_import.py`

## Gaps and Follow-up

- Domain entities are intentionally deferred to the group capability.
