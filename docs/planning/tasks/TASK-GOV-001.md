---
id: TASK-GOV-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-GOV-001
  - FR-GOV-002
  - FR-GOV-003
  - FR-GOV-004
capability: CAP-GOV-001
owner: domain
---

# Task: Add vote-approved rotation governance

## Goal

Allow members to approve a future classic rotation order through an explicit,
threshold-based proposal without changing historical rotations.

## Acceptance Criteria

- [x] Create a rotation-change proposal with proposer, order, deadline, threshold, and effective cycle.
- [x] Record one vote per member with yes, no, or abstain choice.
- [x] Determine approval from the configured threshold.
- [x] Activate an approved order only from its effective cycle.
- [x] Preserve proposal, vote, and rotation provenance in audit records.

## Planned Changes

- `src/tontine/governance/`
- `src/tontine/classic/`
- `tests/governance/`
- `tests/classic/`

## Validation

```text
uv run pytest tests/governance tests/classic
```

## Completion Notes

Implemented provider-independent governance primitives for ruleset versioning, rotation proposals, one-member-one-vote decisions, approval thresholds, effective-cycle activation, and append-only audit events. Authentication and external signatures remain outside the core.
