---
id: TASK-HYB-008
status: ready
started: null
completed: null
adr_refs:
  - ADR-006
requirements:
  - FR-HYB-002
  - FR-HYB-005
  - FR-API-002
  - NFR-TEST-001
capability: CAP-HYB-001
owner: package-boundary
---

# Task: Define the allocation repository contract and audit wiring for adapters

## Goal

Give the Kolo adapter, and any other adapter, a tested contract for the
one-allocation-per-contribution key and the hybrid audit events.

## Context

ADR-006: adapters must enforce one allocation per `contribution_id`, for example
with a unique database constraint. The database constraint itself lives in the
Kolo adapter project, outside `src/tontine/`; this package supplies the protocol,
in-memory implementation, shared contract tests, and audit events it must
satisfy. Depends on TASK-HYB-003, TASK-HYB-004, TASK-HYB-005, and TASK-HYB-006.

## Acceptance Criteria

- [ ] Add an `AllocationRepository` protocol keyed by `contribution_id` with
  documented duplicate, missing-record, immutability, and ordering semantics.
- [ ] Provide a deterministic in-memory implementation that rejects a second
  allocation for the same contribution.
- [ ] Add shared contract tests that any adapter can run against its own
  implementation, including the duplicate-key case.
- [ ] Emit canonical audit events for allocation, reversal, catch-up or forfeit
  election, arrears, and exit, with stable event identifiers.
- [ ] Document for the Kolo adapter the required unique constraint on the
  allocation key and how to run the contract tests.
- [ ] Keep database, framework, and Kolo code outside `src/tontine/`.

## Planned Changes

- `src/tontine/repositories/protocols.py`
- `src/tontine/hybrid/`
- `tests/repositories/test_memory_contracts.py`
- `tests/hybrid/test_audit.py`
- `README.md`

## Validation

```text
uv run pytest tests/repositories tests/hybrid
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Not started. The Kolo database migration is delivered in the Kolo adapter
project against this contract.
