---
id: TASK-API-002
status: backlog
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

- [ ] Define stable public imports without leaking adapter dependencies.
- [ ] Add concise Google-style docstrings to public entry points.
- [ ] Add examples covering classic and investment workflows.
- [ ] Keep authentication and access-control decisions at the consuming application boundary.
- [ ] Test public imports and representative end-to-end domain calls without infrastructure.

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

Backlog item. The public API should be shaped after repository protocols and aggregate boundaries are stable.
