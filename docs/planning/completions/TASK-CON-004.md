---
task: TASK-CON-004
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-CON-004

## Outcome

Contribution rules now configure a penalty destination, and rule-created cycles
carry the applicable penalty amount, currency, grace period, and destination
into late and missed assessments. The public factory preserves the existing
timezone parameter and rejects conflicting timezones or rules not effective on
the cycle start date. Explicit occurrence timestamps and named aware-datetime
validation remain intact.

## Acceptance Criteria Evidence

- [x] Contribution rules accept and validate destinations with
  `COMMON_RESERVE` as the default: `tests/contributions/test_contribution_rules.py`.
- [x] All supported destinations, penalty terms, and late/missed assessments
  pass through `tontine.create_contribution_cycle`: `tests/test_public_api.py`.
- [x] Naive `payment_date`, `as_of`, and `assessed_on` errors identify the field
  and explain aware datetime construction: `tests/contributions/test_contribution_recording.py`
  and `tests/contributions/test_contribution_rules.py`.
- [x] Supplied payment and assessment occurrence times remain on their records:
  `test_penalties_preserve_explicit_occurrence_times` in
  `tests/contributions/test_contribution_recording.py`.
- [x] Public API documentation and BRD describe rule propagation and defaults:
  `src/tontine/__init__.py` and `BRD.md`.

## Validation

```text
uv run pytest
171 passed

uv run ruff check src tests
All checks passed

uv run mypy src
Success: no issues found in 23 source files

uv build
Built source distribution and wheel successfully

uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
72 requirements referenced; 0 uncovered; 0 undefined references.

uv run python .agents/skills/pdlc/scripts/status.py docs/planning
Wrote docs/planning/STATUS.md (64 items).
```

## Files Changed

- `BRD.md`
- `docs/planning/STATUS.md`
- `docs/planning/capabilities/CAP-CON-002.md`
- `docs/planning/tasks/TASK-CON-004.md`
- `docs/planning/completions/TASK-CON-004.md`
- `src/tontine/__init__.py`
- `src/tontine/contributions/__init__.py`
- `tests/contributions/test_contribution_recording.py`
- `tests/contributions/test_contribution_rules.py`
- `tests/test_public_api.py`

## Gaps and Follow-up

None.
