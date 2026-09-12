---
id: TASK-PACKAGE-002
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-PKG-001
  - NFR-PKG-001
capability: CAP-PACKAGE-001
owner: package-foundation
---

# Task: Configure distribution and development tooling

## Goal

Configure `tontine-core` metadata and a minimal Python 3.12+ development stack
for testing, linting, formatting, and type checking.

## Acceptance Criteria

- [x] `pyproject.toml` declares the distribution name `tontine-core`.
- [x] The package requires Python 3.12 or newer.
- [x] Pytest, Ruff, and a type checker are configured as development tools.
- [x] Core runtime dependencies remain empty unless the BRD requires one.
- [x] Tool commands are documented and reproducible in a fresh environment.

## Planned Changes

- `pyproject.toml`
- `README.md`
- `uv.lock`

## Validation

```text
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

## Completion Notes

Added `pyproject.toml` with `tontine-core` distribution metadata, Python 3.12+
support, setuptools build configuration, and uv-managed development dependencies
for pytest, Ruff, mypy, and build. Generated `uv.lock`.

Completion record: `docs/planning/completions/TASK-PACKAGE-002.md`.
