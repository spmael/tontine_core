---
id: TASK-GOV-007
status: ready
started: null
completed: null
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

- [ ] Add a member-exit effect with member, exit type (`voluntary`, `expulsion`, `death`), exit date, and the cycle in which the exit was requested.
- [ ] Add a penalty-waiver effect referencing one penalty assessment.
- [ ] Add a payout-deferral effect referencing one exit, with a required reason and an extended date no later than 24 months after the exit takes effect.
- [ ] Exclude the member concerned from the electorate of an expulsion or of a waiver of their own penalty.
- [ ] Expose approved effects through the existing decision lookup.
- [ ] Tests cover approval, rejection, recusal, electorate snapshots, the exit request cycle, and deferral reason and ceiling.

## Planned Changes

- `src/tontine/governance/`
- `tests/governance/test_member_decisions.py`

## Validation

```text
uv run pytest tests/governance
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Not started.
