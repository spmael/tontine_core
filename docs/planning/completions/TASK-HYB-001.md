---
task: TASK-HYB-001
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-HYB-001

## Outcome

Implemented immutable hybrid policy values and group-owned effective-cycle
schedules, supporting FR-HYB-001 and FR-HYB-003 under ADR-006. No allocation,
unit issuance, financial execution, or persistence adapter was added.

## Acceptance Criteria Evidence

- [x] Integer basis points accept 0 through 10,000 and reject booleans,
  fractional values, and out-of-range values.
- [x] Closed penalty and contribution payment orders preserve the agreed
  defaults and reject fund-first.
- [x] Catch-up policy, exact positive Decimal launch prices, finite percentage
  fees, and valuation age are explicit, validated immutable values.
- [x] Fees are uniform across units, death is fee-free, and changes require a
  full intervening cycle. Tests include inserting before the first scheduled
  rule and preserving notice for already-scheduled future rules.
- [x] Declared legal form and validated statute flags are stored without
  classifying units or making regulatory decisions.
- [x] Excess cooperative expulsion fees raise ValueError; other forms emit an
  observable UserWarning.
- [x] Cycle-end payout defaults to a 12-month maximum; configurations cannot
  pre-authorize extensions. The absolute ceiling is 24 months.
- [x] Schedule resolution uses effective cycle and then version number;
  additions require future activation relative to the supplied current cycle.
  Duplicate versions and cross-currency changes are rejected.
- [x] Optional governance references are stored and reject blank references.
- [x] Currencies without ISO minor units are rejected via the existing currency
  helper.
- [x] Tests cover invalid inputs, missing effective rules, ties, deep
  immutability, public exports, and all rule validation branches.

## Validation

Executed with the configured Python 3.14.2 environment:

```text
uv run pytest tests/hybrid --cov=tontine.hybrid --cov-report=term-missing
61 passed; 100% hybrid line coverage.

uv run pytest tests/hybrid tests/test_import.py tests/test_public_api.py -q
72 passed.

uv run ruff check src tests
All checks passed.

uv run mypy src
Success: no issues found in 32 source files.

uv build
Source distribution and wheel built successfully.

uv run pytest -q
322 passed.

uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
72 of 72 requirements referenced; 0 uncovered; 0 undefined.
```

Re-run on 2026-10-18 during review with identical results. `ruff format
--check` reports nine pre-existing files outside this task; the new hybrid
modules and tests are formatted.

Pylance reported no diagnostics for the new rules module. The editor test runner
did not discover the new test file; direct pytest execution supplied the results
above.

## Files Changed

- `src/tontine/hybrid/rules.py`
- `src/tontine/hybrid/__init__.py`
- `tests/hybrid/test_rules.py`
- `BRD.md`
- `README.md`
- `docs/planning/tasks/TASK-HYB-001.md`
- `docs/planning/capabilities/CAP-HYB-001.md`
- `docs/planning/capabilities/README.md`
- Generated planning status and ADR citation index.

## Gaps and Follow-up

No remaining gaps for this policy task. Governance authorization, request-time
exit-fee selection, deadline calculations, and reasoned deferral extensions are
implemented by the later governance and exit tasks. Schedule construction is a
history-restoration boundary; additions use `with_version` and the caller's
current cycle. This task introduces no repository protocol or implementation;
allocation repository contract tests remain in TASK-HYB-008.
