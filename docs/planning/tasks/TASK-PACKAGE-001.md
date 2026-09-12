---
id: TASK-PACKAGE-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-PKG-001
capability: CAP-PACKAGE-001
owner: package-foundation
---

# Task: Create the `tontine` package layout

## Goal

Create the BRD-recommended `src/tontine/` import package with a stable public
entry point and the initial domain-capability directories.

## Acceptance Criteria

- [x] `src/tontine/__init__.py` imports successfully.
- [x] Initial capability directories are created only where needed.
- [x] The public import name is `tontine`, not `tontine_core`.
- [x] No framework or persistence dependency enters the core package.

## Planned Changes

- `src/tontine/__init__.py`
- `src/tontine/exceptions.py`
- `src/tontine/groups/`
- `src/tontine/members/`
- `tests/test_import.py`

## Validation

```text
uv run python -c "import tontine"
uv run pytest tests/test_import.py
```

## Completion Notes

Created `src/tontine/` with public version metadata, domain exceptions, and
initial group and member package boundaries. Verified with `uv run pytest
tests/test_import.py` and `uv run python -c "import tontine"`.

Completion record: `docs/planning/completions/TASK-PACKAGE-001.md`.
