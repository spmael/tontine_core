---
id: TASK-STATE-005
status: shipped
started: 2026-10-21
completed: 2026-10-21
adr_refs:
  - ADR-007
requirements:
  - FR-LDG-006
  - NFR-PERF-001
capability: CAP-STATE-001
owner: domain
---

# Task: Rebuildable ledger balance projection

## Goal

Avoid rescanning all posted journals for each current balance query while
ensuring the in-memory projection can be deterministically rebuilt from journals.

## Context

ADR-007: immutable journal entries remain the accounting source of truth; a
balance index is derived state and must not become a separately authoritative
balance store.

## Acceptance Criteria

- [x] Maintain current account/currency balances as a derived projection when
  balanced journals are posted.
- [x] Rebuild the projection deterministically from the immutable journal
  sequence, preserving duplicate and validation behavior.
- [x] Keep journal history immutable and expose no operation that directly sets
  a cached balance.
- [x] Prove projection values equal a full journal-derived calculation after
  posts, reversals, adjustments, and rebuild.
- [x] Cover multiple accounts and currencies plus invalid journal handling.

## Planned Changes

- `src/tontine/ledger/__init__.py`
- `tests/ledger/test_ledger_posting.py`
- `tests/ledger/test_ledger_corrections.py`

## Validation

```text
uv run pytest tests/ledger
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Shipped. Point-in-time balance queries remain in CAP-LEDGER-002.
