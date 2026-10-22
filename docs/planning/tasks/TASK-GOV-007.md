---
id: TASK-GOV-007
status: shipped
started: 2026-10-18
completed: 2026-10-18
adr_refs:
  - ADR-006
requirements:
  - FR-HYB-003
  - FR-HYB-004
capability: CAP-HYB-001
owner: domain
---

# Task: Add typed exit and penalty-waiver decisions with recusal

## Goal

Let governance approve member exits and penalty waivers while excluding the interested member from the electorate.

## Context

ADR-006 and ADR-004: typed effects on the reusable decision lifecycle. Every exit (voluntary, expulsion, death) and every penalty waiver needs an approved decision.

## Acceptance Criteria

- [x] Add a member-exit effect with member, exit type (`voluntary`, `expulsion`, `death`), exit date, and the cycle in which the exit was requested.
- [x] Add a penalty-waiver effect referencing one penalty assessment.
- [x] Add a payout-deferral effect referencing one exit, with a required reason and an extended date no later than 24 months after the exit takes effect.
- [x] Exclude the member concerned from the electorate of an expulsion or of a waiver of their own penalty.
- [x] Expose approved effects through the existing decision lookup.
- [x] Tests cover approval, rejection, recusal, electorate snapshots, the exit request cycle, and deferral reason and ceiling.

## Planned Changes

- `src/tontine/governance/`
- `tests/governance/test_member_decisions.py`
- `BRD.md`
- `docs/architecture/adr/ADR-004-governance-decision-lifecycle.md`

## Validation

```text
uv run pytest tests/governance/test_member_decisions.py -q
10 passed.

uv run pytest tests/governance -q
44 passed.

uv run ruff check src tests
All checks passed.

uv run ruff format --check src/tontine/governance tests/governance
13 files already formatted.

uv run mypy src
Success: no issues found in 37 source files.

uv run pytest -q
391 passed.

uv build -o /tmp/gov007-dist
Source distribution and wheel built successfully.

git diff --check
Passed.
```

## Completion Notes

Typed effects record approved exits, penalty waivers, and reasoned payout
deferrals. Expulsion subjects and members whose own penalties are waived are
excluded from the frozen electorate. Cycle-effective rules retain their
future-cycle requirement; these member decisions apply in the current cycle.
See [completion evidence](../completions/TASK-GOV-007.md).
