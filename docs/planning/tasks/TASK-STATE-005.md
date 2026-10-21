---
id: TASK-STATE-005
status: ready
started: null
completed: null
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

- [ ] Maintain current account/currency balances as a derived projection when
  balanced journals are posted.
- [ ] Rebuild the projection deterministically from the immutable journal
  sequence, preserving duplicate and validation behavior.
- [ ] Keep journal history immutable and expose no operation that directly sets
  a cached balance.
- [ ] Prove projection values equal a full journal-derived calculation after
  posts, reversals, adjustments, and rebuild.
- [ ] Cover multiple accounts and currencies plus invalid journal handling.

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

Ready. Point-in-time balance queries remain in CAP-LEDGER-002.
