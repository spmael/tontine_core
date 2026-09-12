---
id: TASK-PACKAGE-003
status: backlog
requirements:
  - FR-PKG-001
  - NFR-PKG-001
  - NFR-TEST-001
capability: CAP-PACKAGE-001
owner: package-foundation
---

# Task: Add package smoke checks

## Goal

Prove that the distribution, import path, and isolated test workflow work before
domain behavior is implemented.

## Acceptance Criteria

- [ ] The package imports from the `src/` layout in the configured test environment.
- [ ] A minimal pytest smoke test passes without a database or web framework.
- [ ] A source distribution and wheel can be built locally.
- [ ] The README shows the correct installation and import commands.

## Planned Changes

- `tests/test_import.py`
- `README.md`
- Build metadata or CI configuration if introduced by TASK-PACKAGE-002.

## Validation

```text
python -m pytest tests/test_import.py
python -m build
```

## Completion Notes

Not started.
