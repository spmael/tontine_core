---
id: TASK-PACKAGE-001
status: ready
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

- [ ] `src/tontine/__init__.py` imports successfully.
- [ ] Initial capability directories are created only where needed.
- [ ] The public import name is `tontine`, not `tontine_core`.
- [ ] No framework or persistence dependency enters the core package.

## Planned Changes

- `src/tontine/__init__.py`
- `src/tontine/exceptions.py`
- `src/tontine/groups/`
- `src/tontine/members/`
- `tests/test_import.py`

## Validation

```text
python -c "import tontine"
python -m pytest tests/test_import.py
```

## Completion Notes

Not started.
