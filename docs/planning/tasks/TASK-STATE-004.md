---
id: TASK-STATE-004
status: ready
started: null
completed: null
adr_refs:
  - ADR-007
requirements:
  - FR-API-004
capability: CAP-STATE-001
owner: domain
---

# Task: Snapshot hybrid exit registry state

## Goal

Capture and restore exit settlements and queue reports without rerunning
governance approval or settlement calculations.

## Context

ADR-007: snapshots restore the exact recorded state and preserve provenance.
Exit restoration depends on the allocation, arrears, and unit-ledger snapshots.

## Acceptance Criteria

- [ ] Snapshot every recorded exit, settlement status and lines, queue report,
  and audit provenance needed to preserve deterministic output.
- [ ] Restore against matching allocation, arrears, and unit-ledger state without
  recalculating a valuation, fee, arrears offset, or external payment.
- [ ] Reject unsupported schemas and inconsistent exit-to-proposal, allocation,
  arrears, or unit-event references.
- [ ] Preserve queue ordering and allow valid future exit status transitions.
- [ ] Cover round trips, pending and settled exits, queue reports, invalid state,
  and public imports.

## Planned Changes

- `src/tontine/hybrid/exit.py`
- `src/tontine/hybrid/exit_models.py`
- `src/tontine/hybrid/snapshots.py`
- `tests/hybrid/test_state_snapshots.py`

## Validation

```text
uv run pytest tests/hybrid
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Ready after TASK-STATE-001 through TASK-STATE-003.
