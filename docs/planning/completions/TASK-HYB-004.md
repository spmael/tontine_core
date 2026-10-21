---
task: TASK-HYB-004
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-HYB-004

## Outcome

Implemented linked, append-only reversals for recorded hybrid allocations.
Each reversal preserves the original allocation and its unit price while
recording negative offsets for the pot, fund, issued units, and cash residual.
Unit cancellation is validated before the reversal identifier is consumed, so
a failed reversal can be retried. Reversing an allocation releases its
cycle/member source key for a corrected contribution with a new identifier.

## Acceptance Criteria Evidence

- [x] Each reversal records its allocation link, reason, aware timestamp, and
  exact negative offsets.
- [x] Reversals cancel the original amounts and units without repricing.
- [x] A second reversal and a reversal of an unknown allocation are rejected.
- [x] Corrected contributions can be allocated after reversal with a new
  contribution identifier.
- [x] Replay verifies the reversal against the original allocation before
  changing derived unit balances.
- [x] Tests cover duplicate identifiers, zero-unit reversals, failed-cancellation
  retries, linkage, replay, and derived balances.

## Validation

```text
uv run pytest tests/hybrid tests/investments/test_units.py -q
123 passed.

uv run ruff check src tests
All checks passed.

uv run ruff format --check src/tontine/hybrid src/tontine/investments/valuation.py tests/hybrid tests/investments/test_units.py
All files formatted.

uv run mypy src
Success: no issues found in 36 source files.

uv run pytest -q
381 passed.

uv build -o /tmp/hyb004-dist
Source distribution and wheel built successfully.

uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
72 of 72 requirements referenced; 0 uncovered; 0 undefined.

git diff --check
Passed.
```

## Files Changed

- `src/tontine/hybrid/allocation.py`
- `src/tontine/hybrid/allocation_models.py`
- `src/tontine/hybrid/allocation_registry.py`
- `src/tontine/hybrid/__init__.py`
- `src/tontine/investments/valuation.py`
- `tests/hybrid/test_reversal.py`
- `tests/investments/test_units.py`
- `BRD.md`
- `README.md`
- `docs/planning/tasks/TASK-HYB-004.md`
- `docs/planning/capabilities/CAP-HYB-001.md`
- `docs/planning/STATUS.md`

## Gaps and Follow-up

Persistent repository constraints and shared adapter contract tests remain in
TASK-HYB-008. Late and missed contributions, member exits, and combined
settlement reporting remain in subsequent hybrid tasks.
