---
id: TASK-API-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-API-001
  - FR-API-002
  - NFR-TEST-001
capability: CAP-API-001
owner: package-boundary
---

# Task: Define repository protocols and in-memory contracts

## Goal

Formalize repository interfaces without coupling the domain to a database,
web framework, or external service.

## Acceptance Criteria

- [x] Define small protocols for group, member, contribution/cycle, account, ledger, investment, Classic, Governance, and Audit boundaries.
- [x] Define duplicate, missing-record, deterministic-order, and adapter-boundary semantics.
- [x] Provide deterministic in-memory implementations for group, member, account, cycle, Classic, Governance, and Audit boundaries.
- [x] Add focused contract tests that run without infrastructure.
- [x] Formalize member, Classic, Governance, and Audit protocol boundaries.
- [x] Document future SQL, Django, SQLAlchemy, and other adapters as external implementations.

## Planned Changes

- `src/tontine/repositories/`
- `tests/repositories/`
- `docs/architecture/`

## Validation

```text
uv run pytest tests/repositories
uv run ruff check src/tontine/repositories tests/repositories
uv run mypy src/tontine/repositories
```

## Completion Notes

Implemented formal group, member, account, cycle, ledger, investment, Classic, Governance, and Audit repository protocols; deterministic in-memory implementations; shared repository contract tests; and adapter-boundary documentation. Database and framework adapters remain outside the core.
