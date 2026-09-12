---
id: TASK-API-001
status: backlog
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

- [ ] Define small protocols for group, contribution/cycle, account, ledger, and investment boundaries.
- [ ] Define stable ID, duplicate, missing-record, immutability, and deterministic-order semantics.
- [ ] Provide in-memory implementations or adapt existing stores behind the protocols.
- [ ] Add shared contract tests that run without infrastructure.
- [ ] Document adapter boundaries for SQL, Django, SQLAlchemy, and other future implementations.

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

Backlog item. Do not create empty repository modules solely to mirror the BRD tree; add protocols when their aggregate semantics and contract tests are defined.
