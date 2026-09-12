---
task: TASK-PACKAGE-002
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-PACKAGE-002

## Outcome

Configured `tontine-core` distribution metadata, Python 3.12+ support, setuptools
build metadata, and uv-managed development dependencies.

## Acceptance Criteria Evidence

- [x] `pyproject.toml` declares distribution name `tontine-core`: `[project].name`.
- [x] Package requires Python 3.12 or newer: `[project].requires-python`.
- [x] Pytest, Ruff, and mypy are configured: `[dependency-groups].dev` and tool sections.
- [x] Runtime dependencies remain empty: `[project].dependencies = []`.
- [x] Tool commands are reproducible: `uv.lock` and README workflow.

## Validation

```text
uv lock
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv build
```

All checks passed.

## Files Changed

- `pyproject.toml`
- `uv.lock`
- `README.md`

## Gaps and Follow-up

- CI automation can be added after the first domain capability is implemented.
