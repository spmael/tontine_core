---
id: CAP-GOV-002
status: backlog
started: null
completed: null
adr_refs: []
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

- [ ] Support decision proposals whose approved effects are not inherently
  rotation changes.
- [ ] Expose eligible, yes, no, abstain, and not-voted counts with evaluation
  outcomes.
- [ ] Apply explicit threshold, quorum, participation, and proposal-closing
  policies.
- [ ] Preserve proposal eligibility context across later membership changes.
- [ ] Validate future effective cycles and provide actionable domain errors.
- [ ] Reject votes after the deadline and preserve caller-supplied audit times.
- [ ] Support a one-cycle rotation exception without replacing the base order.

## Implementation Tasks

Task decomposition is intentionally deferred until the open policy decisions in
[`../../architecture/next-version-gap-architecture.md`](../../architecture/next-version-gap-architecture.md)
are reviewed.

## Verification

- Unit tests: proposal lifecycle, membership changes, deadline boundaries,
  tally/quorum cases, cycle validation, explicit times, and exception scope.
- Integration tests: public governance API tests with an approved rotation effect
  and a non-rotation decision.
- Manual review: approval policy, electorate semantics, and decision-effect
  provenance.
