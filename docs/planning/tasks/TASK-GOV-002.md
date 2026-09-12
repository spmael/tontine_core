---
id: TASK-GOV-002
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-GOV-004
  - NFR-TEST-001
capability: CAP-GOV-001
owner: domain
---

# Task: Add cross-capability audit event registry

## Goal

Provide one append-only audit stream for significant group, membership,
contribution, payout, investment, valuation, governance, and ledger events while
preserving each domain record's own provenance.

## Acceptance Criteria

- [x] Define an immutable audit event with event ID, type, aggregate, timestamp, actor, source event, and details.
- [x] Record governance, group, member, contribution, payout, investment, valuation, and ledger correction events.
- [x] Reject duplicate audit event identifiers.
- [x] Preserve deterministic event ordering and allow aggregate-specific history queries.
- [x] Add contract tests without a database, network, authentication, or external signatures.

## Planned Changes

- `src/tontine/audit/`
- `src/tontine/governance/`
- `tests/audit/`

## Validation

```text
uv run pytest tests/audit tests/governance
uv run ruff check src/tontine/audit tests/audit
uv run mypy src/tontine/audit
```

## Completion Notes

Implemented an immutable cross-capability audit event registry with deterministic append ordering, aggregate-specific history queries, and duplicate-ID protection. Domain records retain their own provenance; the registry provides a unified audit stream.
