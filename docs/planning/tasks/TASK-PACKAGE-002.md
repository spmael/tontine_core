---
id: TASK-PACKAGE-002
status: backlog
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

- [ ] `pyproject.toml` declares the distribution name `tontine-core`.
- [ ] The package requires Python 3.12 or newer.
- [ ] Pytest, Ruff, and a type checker are configured as development tools.
- [ ] Core runtime dependencies remain empty unless the BRD requires one.
- [ ] Tool commands are documented and reproducible in a fresh environment.

## Planned Changes

- `pyproject.toml`
- `README.md`
- `uv.lock` or another lock file only if the chosen workflow requires it

## Validation

```text
python -m pytest
ruff check .
ruff format --check .
```

## Completion Notes

Not started.
