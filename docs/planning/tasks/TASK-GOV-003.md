---
id: TASK-GOV-003
status: shipped
started: 2026-10-18
completed: 2026-10-18
requirements:
  - FR-GOV-006
  - FR-GOV-007
  - FR-GOV-008
  - FR-GOV-009
  - FR-GOV-011
capability: CAP-GOV-002
adr_refs:
  - ADR-004
owner: domain
---

# Task: Add explicit proposal eligibility and approval rules

## Goal

Make proposal electorate, quorum, evaluation timing, effective-cycle validation,
and audit occurrence times explicit and reproducible.

## Context

Proposal electorate is frozen at creation. Yes votes remain measured against the
eligible electorate, quorum is two-thirds rounded up, abstentions count only
toward quorum, and early evaluation requires every eligible member to have voted.

## Acceptance Criteria

- [x] Capture the proposal electorate and current cycle at creation.
- [x] Expose eligible, yes, no, abstain, non-voting, quorum, and approval-threshold
  tally results.
- [x] Apply the two-thirds quorum and abstention policy consistently.
- [x] Reject votes after the deadline and reject early evaluation before
  full participation.
- [x] Require a strictly future effective cycle and actionable cycle errors.
- [x] Require explicit timezone-aware occurrence times for mutating operations.
- [x] Test membership changes, quorum boundaries, deadline boundaries, and
  lifecycle invalid transitions.

## Planned Changes

- `src/tontine/governance/`
- `tests/governance/`

## Validation

```text
uv run pytest tests/governance/test_governance.py tests/governance/test_proposal_policies.py
uv run ruff check src/tontine/governance tests/governance
uv run mypy src/tontine/governance
```

## Completion Notes

Existing threshold-only behavior remains representable with an explicitly
configured zero quorum. See `docs/planning/completions/TASK-GOV-003.md`.
