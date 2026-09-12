---
id: TASK-PACKAGE-003
status: shipped
started: 2026-09-12
completed: 2026-09-12
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

- [x] The package imports from the `src/` layout in the configured test environment.
- [x] A minimal pytest smoke test passes without a database or web framework.
- [x] A source distribution and wheel can be built locally.
- [x] The README shows the correct installation and import commands.

## Planned Changes

- `tests/test_import.py`
- `README.md`
- Build metadata or CI configuration if introduced by TASK-PACKAGE-002.

## Validation

```text
uv run pytest tests/test_import.py
uv build
```

## Completion Notes

Added the package import smoke test and documented the uv workflow in `README.md`.
Verified `uv run pytest`, Ruff check and format checks, mypy, and `uv build`.

Completion record: `docs/planning/completions/TASK-PACKAGE-003.md`.
