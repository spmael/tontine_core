---
id: CAP-GOV-002
status: shipped
started: 2026-10-18
completed: 2026-10-18
adr_refs:
  - ADR-004
depends_on:
  - CAP-GOV-001
  - CAP-CLASSIC-002
blocks: []
requirements:
  - FR-GOV-005
  - FR-GOV-006
  - FR-GOV-007
  - FR-GOV-008
  - FR-GOV-009
  - FR-GOV-010
  - FR-GOV-011
owner: domain
---

# Capability: Reusable Governance Decisions

## Outcome

A consumer can propose and evaluate rotation and non-rotation decisions using
explicit eligibility, approval, cycle, deadline, and occurrence-time context.

## Domain Boundary

- Inputs: decision proposals, electorate context, approval rules, votes, effective
  cycles, and explicit timestamps
- Outputs: decision status, auditable tallies, approved effects, and audit events
- Invariants: vote eligibility is reproducible; decision effects are explicit;
  actions after deadlines are rejected; audit time is supplied rather than
  regenerated during replay
- Exclusions: application authentication, external signatures, hidden wall-clock
  behavior, and untyped execution of arbitrary proposal payloads

## Acceptance Criteria

- [x] Support decision proposals whose approved effects are not inherently
  rotation changes.
- [x] Expose eligible, yes, no, abstain, and not-voted counts with evaluation
  outcomes.
- [x] Apply explicit threshold, quorum, participation, and proposal-closing
  policies.
- [x] Preserve proposal eligibility context across later membership changes.
- [x] Validate future effective cycles and provide actionable domain errors.
- [x] Reject votes after the deadline and preserve caller-supplied audit times.
- [x] Support a one-cycle rotation exception without replacing the base order.

## Implementation Tasks

- [x] [TASK-GOV-003](../tasks/TASK-GOV-003.md): Add explicit proposal
  eligibility, approval rules, deadlines, and evaluation tallies.
- [x] [TASK-GOV-004](../tasks/TASK-GOV-004.md): Add typed governance effects for
  rotation exceptions and ruleset activation.
- [x] [TASK-GOV-005](../tasks/TASK-GOV-005.md): Add versioned governance
  snapshots and deterministic rehydration.

## Verification

- Unit tests cover proposal lifecycle, membership changes, deadline boundaries,
  two-thirds quorum/tally cases, cycle validation, snapshot restoration, and
  exception scope.
- Public governance API tests cover approved/rejected rotation, exception, and
  ruleset effects, plus deterministic snapshot rehydration.
- Manual review confirms electorate stability, explicit decision provenance,
  and the persistence-adapter boundary.
