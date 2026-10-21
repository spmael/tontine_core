---
task: TASK-HYB-005
started: 2026-10-18
completed: 2026-10-18
status: shipped
---

# Completion: Apply partial payments, arrears, catch-up, and collateral

## Outcome

Hybrid cycle closure records unpaid rotation, fund, and penalty amounts. The
registry applies already-received payments under effective penalty and
contribution orders, stores the rule version, and derives remaining arrears
from the original record and subsequent events. Missed contributions issue no
units.

Members can elect catch-up or forfeit before the cycle deadline. Catch-up units
use the payment-date valuation or remain pending until a usable valuation can
be applied. Deadline defaults and disabled catch-up forfeit only the unpaid
fund share. Approved governance decisions are required to waive penalties.
Rotation arrears block redemption through the hybrid registry, and unit offsets
require an explicit valuation reference.

## Evidence

- Catch-up allocations are tagged with their arrears source and share the
  existing append-only allocation reversal path.
- Cycle closure, elections, payment applications, waivers, forfeitures, and unit
  offsets produce audit events.
- Penalty destinations include `ROTATION_POT`; the existing
  `COMMON_RESERVE` default is unchanged.
- No payment initiation or fund movement was added.
- Focused arrears, allocation, reversal, and contribution tests passed.
- Full test suite: `407 passed`.
- Ruff: passed for `src` and `tests`.
- Mypy: passed for all 38 source files.
- Package build: source distribution and wheel built successfully.
- Requirement traceability: all 72 defined requirements covered; no undefined
  references.

## Validation commands

```text
uv run pytest -q
uv run ruff check src tests
uv run mypy src
uv build
uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
```

## Changed files

- `BRD.md`
- `docs/planning/capabilities/CAP-HYB-001.md`
- `docs/planning/tasks/TASK-HYB-005.md`
- `src/tontine/contributions/__init__.py`
- `src/tontine/hybrid/__init__.py`
- `src/tontine/hybrid/allocation.py`
- `src/tontine/hybrid/allocation_models.py`
- `src/tontine/hybrid/allocation_registry.py`
- `src/tontine/hybrid/arrears.py`
- `tests/hybrid/test_arrears.py`

## Remaining gaps

No acceptance criteria remain for this task. Member exit, combined settlement
reporting, and persistence-adapter contracts remain in their separately planned
tasks.
