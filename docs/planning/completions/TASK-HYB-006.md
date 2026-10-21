---
task: TASK-HYB-006
started: 2026-10-18
completed: 2026-10-18
status: shipped
---

# Completion: Record member exit and entitlement

## Outcome

Approved governance exits are recorded with the rule and exit-fee schedule
effective in the request cycle. The allocation registry freezes new unit
issuance from the exit date. Exit settlement waits for an available forward
valuation, derives excess pot received from recorded contribution cycles and
classic payouts, records explicit arrears set-offs, and leaves any negative
net visible as member debt.

Positive exit values become payout entitlements. Death entitlements require a
succession reference before entering the queue, and disputed claims can be
marked consigned with a deposit or sequestration reference. FIFO queue reports
apply a supplied liquidity cap. Recording an external payment reference does
not initiate a transfer.

## Acceptance Criteria Evidence

- [x] Only approved governance exit decisions can be recorded; allocations dated
  on or after the exit date are blocked.
- [x] Forward valuation uses the earliest eligible recorded valuation and
  remains pending until a valuation is effective and available.
- [x] Settlement lines include gross unit value, fee, arrears, and excess pot
  received in order; negative net values remain member debt.
- [x] Fee schedule is captured from the request-cycle rule version, credited to
  the fund, and death exits are fee-free.
- [x] Death proof, disputed-claim consignment, and external payment references
  are explicit status transitions.
- [x] Cycle-end payout dates, approved reasoned extensions, 12-month default
  limit, and 24-month hard limit are validated.
- [x] Liquidity reports preserve FIFO order and do not bypass an earlier
  entitlement that exceeds the remaining cap.
- [x] Tests cover voluntary, expulsion, and death exits; fees; deferrals;
  pending and future valuations; arrears offsets; excess pot; negative net;
  estate proof; consignment; and queue behavior.

## Validation

```text
./.venv/bin/python -m pytest -q
420 passed.

uv run ruff check src tests
All checks passed.

uv run ruff format --check src/tontine/hybrid/exit.py src/tontine/hybrid/exit_models.py src/tontine/hybrid/_exit_calculations.py src/tontine/hybrid/arrears.py src/tontine/hybrid/allocation_registry.py src/tontine/hybrid/__init__.py tests/hybrid/test_exit.py tests/hybrid/test_arrears.py
All changed Python files are formatted.

uv run mypy src
Success: no issues found in 41 source files.

uv build -o /tmp/hyb006-dist-final
Source distribution and wheel built successfully.

uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
72 of 72 requirements referenced; 0 uncovered; 0 undefined.

git diff --check
Passed.
```

The repository-wide `ruff format --check src tests` also reported nine
pre-existing unformatted files outside this task; those files were not changed.

## Files Changed

- `docs/architecture/adr/ADR-006-hybrid-contribution-allocation.md`
- `docs/planning/STATUS.md`
- `docs/planning/capabilities/CAP-HYB-001.md`
- `docs/planning/tasks/TASK-HYB-006.md`
- `src/tontine/hybrid/__init__.py`
- `src/tontine/hybrid/_exit_calculations.py`
- `src/tontine/hybrid/allocation_registry.py`
- `src/tontine/hybrid/arrears.py`
- `src/tontine/hybrid/exit.py`
- `src/tontine/hybrid/exit_models.py`
- `tests/hybrid/test_arrears.py`
- `tests/hybrid/test_exit.py`

## Remaining Gaps

Combined settlement reporting and the allocation repository contract remain in
TASK-HYB-007 and TASK-HYB-008.
