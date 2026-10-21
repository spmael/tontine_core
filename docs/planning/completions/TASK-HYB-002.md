---
task: TASK-HYB-002
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-HYB-002

## Outcome

Implemented a pure split of an amount actually received into rotation-pot and
investment-fund shares under ADR-006. The fund share is rounded down to the
currency's smallest ISO 4217 unit; the pot receives the remainder. No expected
amount, contribution record, posting, allocation, or unit issuance is changed.

## Acceptance Criteria Evidence

- [x] The public `split_contribution` function uses received amount, currency,
  and integer basis points from 0 through 10,000.
- [x] The fund share is rounded down to its currency minor unit and the pot is
  the exact remainder.
- [x] A Hypothesis property test verifies pot plus fund equals received for
  XAF and EUR amounts across the complete basis-point range.
- [x] Explicit tests cover zero and full fund shares, both currencies' smallest
  units, and fund-share rounding.
- [x] Negative, non-finite, and below-minor-unit amounts are rejected.
- [x] The public docstring states the units, return order, rounding, and ADR-006
  rule.
- [x] Hypothesis is declared only in the development dependency group.

## Validation

```text
uv run pytest tests/hybrid
88 passed.

uv run ruff check src tests
All checks passed.

uv run ruff format --check src/tontine/hybrid tests/hybrid
5 files already formatted.

uv run mypy src
Success: no issues found in 33 source files.

uv run pytest -q
349 passed.

uv build -o /tmp/hyb002-dist
Source distribution and wheel built successfully.

uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
72 of 72 requirements referenced; 0 uncovered; 0 undefined.
```

## Files Changed

- `src/tontine/hybrid/split.py`
- `src/tontine/hybrid/__init__.py`
- `tests/hybrid/test_split.py`
- `pyproject.toml` and `uv.lock`
- `README.md`
- `BRD.md`
- `docs/planning/tasks/TASK-HYB-002.md`
- `docs/planning/capabilities/CAP-HYB-001.md`
- Generated planning status and capability indexes.

## Gaps and Follow-up

Contribution recording, allocation events, and unit issuance remain in
TASK-HYB-003 and later tasks.
