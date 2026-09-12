---
id: TASK-API-002
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-API-001
  - FR-API-003
  - NFR-DOC-001
  - NFR-SEC-001
capability: CAP-API-001
owner: package-boundary
---

# Task: Define readable public API boundaries

## Goal

Expose typed, documented package entry points for creating groups, recording
contributions, posting financial events, and consuming structured results.

## Acceptance Criteria

- [x] Define stable public imports without leaking adapter dependencies.
- [x] Add concise Google-style docstrings to public entry points.
- [x] Add examples covering classic and investment workflows.
- [x] Keep authentication and access-control decisions at the consuming application boundary.
- [x] Test public imports and representative end-to-end domain calls without infrastructure.

## Planned Changes

- `src/tontine/__init__.py`
- `examples/`
- `tests/test_public_api.py`
- `README.md`

## Validation

```text
uv run pytest tests/test_import.py tests/test_public_api.py
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Added stable top-level imports and group/cycle creation helpers, public API tests, and a framework-independent Classic/Investment example. Authentication and access control remain application concerns.
