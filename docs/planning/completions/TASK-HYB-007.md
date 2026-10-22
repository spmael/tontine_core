---
task: TASK-HYB-007
started: 2026-10-18
completed: 2026-10-18
status: shipped
---

# Completion: Report the combined settlement position

## Outcome

Added an immutable snapshot of hybrid settlement events and a pure projection
that derives dues, arrears, penalties, rotation position, units, and valuation
from recorded history. Member statements now present the settlement position,
pending events, and statute-derived unit liability treatment without storing
legal/accounting classification in the domain model.

## Acceptance Criteria Evidence

- [x] Derive dues, penalties, rotation amounts, units, and unit value from
  recorded events: `settlement_position` and
  `test_settlement_position_reports_event_derived_hybrid_history`.
- [x] Show pending allocations, exits, elections, and offsets: statement
  `event_lines` assertions in `tests/hybrid/test_settlement.py`.
- [x] Present redeemable units with a statute-derived liability flag and rank
  the pot first: statement priority assertions and
  `test_unconditional_redemption_refusal_changes_default_unit_liability_flag`.
- [x] Extend member reporting and preserve event lineage:
  `HybridSettlementPresentation` and the end-to-end member-statement test.
- [x] Cover mutable contribution-cycle snapshot behavior:
  `test_settlement_history_snapshots_mutable_contribution_cycles`.
- [x] Update the BRD and README with current settlement reporting behavior.

## Validation

```text
uv run pytest
423 passed.

uv run ruff check src tests
All checks passed.

uv run ruff format --check src/tontine/hybrid/__init__.py src/tontine/hybrid/settlement.py src/tontine/hybrid/settlement_history.py tests/hybrid/test_settlement.py
4 files already formatted.

uv run mypy src
Success: no issues found in 43 source files.

uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
72 requirements referenced; 0 uncovered; 0 undefined.

uv run python .agents/skills/pdlc/scripts/status.py docs/planning
Regenerated docs/planning/STATUS.md (78 items).

git diff --check
Passed.
```

## Files Changed

- `BRD.md`
- `README.md`
- `docs/planning/capabilities/CAP-HYB-001.md`
- `docs/planning/STATUS.md`
- `docs/planning/tasks/TASK-HYB-007.md`
- `src/tontine/hybrid/__init__.py`
- `src/tontine/hybrid/settlement.py`
- `src/tontine/hybrid/settlement_history.py`
- `src/tontine/reporting/__init__.py`
- `tests/hybrid/test_settlement.py`

## Gaps and Follow-up

- The allocation repository contract and adapter audit wiring remain in
  TASK-HYB-008.
