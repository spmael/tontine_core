---
task: TASK-HYB-008
started: 2026-10-18
completed: 2026-10-18
status: shipped
---

# Completion: Define the allocation repository contract and audit wiring

## Outcome

Defined a public repository protocol keyed by contribution identifier and a
deterministic in-memory implementation. Immutable allocation records can be
inserted once; a pending allocation can only transition to a resolved record
when all source, rule, and split provenance is preserved. Added a reusable
conformance helper for external adapters.

Allocation and reversal events now enter the canonical audit stream with stable
identifiers. Pending allocation attempts are not logged repeatedly; an initial
pending record and its eventual resolution each produce one event. Existing
arrears, catch-up/forfeit, and exit audit events are covered by assertions.
README guidance documents the `contribution_id` unique constraint required in
persistent adapters and how adapter tests can run the shared contract.

## Acceptance Criteria Evidence

- [x] Public `AllocationRepository` defines key, missing-record, duplicate,
  immutable-transition, and deterministic-order semantics.
- [x] `InMemoryAllocationRepository` enforces unique contribution keys and the
  one-way, provenance-preserving pending-to-resolved transition.
- [x] The reusable contract in
  `tests/repositories/allocation_repository_contract.py` covers ordering,
  missing and duplicate keys, frozen records, and valid/invalid resolution.
- [x] `tests/hybrid/test_audit.py` verifies stable event identifiers and order
  for pending, resolved, and reversed allocations; arrears/election/forfeit and
  exit event types are asserted in their corresponding hybrid tests.
- [x] README adapter guidance requires a persistent unique constraint on
  `contribution_id` and documents running or reusing the contract.
- [x] No persistence framework, database, or Kolo code was added under
  `src/tontine/`.

## Validation

```text
uv run pytest
425 passed.

uv run ruff check src tests
All checks passed.

uv run ruff format --check src/tontine/repositories/__init__.py src/tontine/repositories/protocols.py src/tontine/hybrid/allocation_registry.py tests/repositories/allocation_repository_contract.py tests/repositories/test_allocation_repository_contract.py tests/hybrid/test_audit.py tests/hybrid/test_arrears.py tests/hybrid/test_exit.py
8 changed Python files already formatted.

uv run mypy src
Success: no issues found in 43 source files.

uv run python -c "from tontine.repositories import AllocationRepository, InMemoryAllocationRepository; print(isinstance(InMemoryAllocationRepository(), AllocationRepository))"
True.

uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
72 requirements referenced; 0 uncovered; 0 undefined.

uv run python .agents/skills/pdlc/scripts/status.py docs/planning
Regenerated docs/planning/STATUS.md.

git diff --check
Passed.
```

## Files Changed

- `README.md`
- `docs/planning/STATUS.md`
- `docs/planning/capabilities/CAP-HYB-001.md`
- `docs/planning/tasks/TASK-HYB-008.md`
- `docs/planning/completions/TASK-HYB-008.md`
- `src/tontine/hybrid/allocation_registry.py`
- `src/tontine/repositories/__init__.py`
- `src/tontine/repositories/protocols.py`
- `tests/hybrid/test_audit.py`
- `tests/hybrid/test_arrears.py`
- `tests/hybrid/test_exit.py`
- `tests/repositories/allocation_repository_contract.py`
- `tests/repositories/test_allocation_repository_contract.py`

## Gaps and Follow-up

- The Kolo adapter must implement the protocol and enforce the documented
  database unique constraint in its own repository.
