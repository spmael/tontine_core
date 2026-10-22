---
task: TASK-HYB-003
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-HYB-003

## Outcome

Implemented immutable allocation records from recorded contribution receipts,
valuation-based pricing, pending valuation handling, four-decimal unit
issuance, and in-memory duplicate protection. Each allocation preserves the
source identifiers, rule and payment-order versions, split, price, valuation
reference, issued units, and fund cash residual.

Partial receipts use the recorded rule's contribution order: pot-first applies
the received amount to the expected pot share before the fund, while pro-rata
splits the receipt by basis points. When no units are outstanding, the launch
price is used. If units already exist and no fresh valuation is available, the
fund share remains pending; resolving it uses a valuation available on or
before the resolution date and records that date without changing the receipt
date.

## Acceptance Criteria Evidence

- [x] Allocation requires a recorded paid, partial, or late contribution with
  an actual amount and payment date.
- [x] Duplicate allocations are rejected by contribution ID and by the
  underlying cycle/member source identity.
- [x] Immutable allocation records retain the source, member, cycle, version,
  valuation, price, split, units, and residual.
- [x] The latest usable valuation on or before the pricing date is selected;
  the launch price is used when no units are outstanding.
- [x] Contributions awaiting an absent or stale valuation remain pending and
  resolve using a later valuation without backdating.
- [x] Units are rounded down to four decimal places and any residual is stored
  as fund cash.
- [x] `MemberUnitLedger.issue_units` records positive units with the allocation
  identifier as the unit event reference.
- [x] Tests cover duplicate protection, pending and stale valuations, launch
  price, partial-payment orders, rounding, residual cash, and replay from the
  stored allocation without looking up rules or valuations.

## Validation

```text
uv run pytest tests/hybrid tests/investments/test_units.py -q
113 passed.

uv run ruff check src tests
All checks passed.

uv run mypy src
Success: no issues found in 36 source files.

uv run pytest -q
371 passed.

uv build -o /tmp/hyb003-dist
Source distribution and wheel built successfully.

uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
72 of 72 requirements referenced; 0 uncovered; 0 undefined.
```

## Files Changed

- `src/tontine/hybrid/allocation.py`
- `src/tontine/hybrid/allocation_models.py`
- `src/tontine/hybrid/allocation_registry.py`
- `src/tontine/hybrid/__init__.py`
- `src/tontine/investments/valuation.py`
- `tests/hybrid/test_allocation.py`
- `tests/investments/test_units.py`
- `BRD.md`
- `README.md`
- `docs/planning/tasks/TASK-HYB-003.md`
- `docs/planning/capabilities/CAP-HYB-001.md`
- Generated planning status.

## Gaps and Follow-up

Persistent repository constraints and shared adapter contract tests remain in
TASK-HYB-008. Reversals and corrections remain in TASK-HYB-004.
