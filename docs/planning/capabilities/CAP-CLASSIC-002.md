---
id: CAP-CLASSIC-002
status: shipped
started: 2026-10-18
completed: 2026-10-18
adr_refs: []
depends_on:
  - CAP-CLASSIC-001
blocks: []
requirements:
  - FR-CLS-005
  - FR-GOV-010
owner: domain
---

# Capability: Versioned Rotations and Exceptions

## Outcome

A consumer can resolve the immutable rotation order applicable to a cycle
without loading governance history and can represent a separately approved,
single-cycle exception without mutating the base order.

## Domain Boundary

- Inputs: effective-cycle rotation versions and approved, cycle-scoped exceptions
- Outputs: deterministic base rotation version and selected recipient for a cycle
- Invariants: resolution uses the latest applicable version; historical orders
  remain unchanged; a higher version breaks an effective-cycle tie; exceptions
  replace only one cycle's recipient and do not leak into other cycles
- Exclusions: proposal voting, randomized order generation, payment execution,
  and persistence adapters

## Acceptance Criteria

- [x] Resolve a cycle's order from rotation versions independently of proposal
  and vote replay.
- [x] Keep version ordering deterministic for equal or conflicting effective
  cycles by selecting the highest version number at the latest effective cycle.
- [x] Represent an approved one-cycle exception without changing the base order.
- [x] Reject invalid rotation orders, exception recipients, and exception cycle
  scope.
- [x] Preserve historical rotation resolution after later versions are added.

## Implementation Tasks

- [x] [TASK-CLASSIC-005](../tasks/TASK-CLASSIC-005.md): Add immutable
  effective-cycle rotation versions.
- [x] [TASK-CLASSIC-006](../tasks/TASK-CLASSIC-006.md): Apply approved one-cycle
  recipient overrides.

## Verification

- Unit tests: `tests/classic/test_rotation_schedule.py` covers effective-cycle
  resolution, deterministic version ties, invalid versions, exception scope,
  payout/policy invariants, and restoration of the base order.
- Public API tests construct and resolve the schedule without a governance
  registry; proposal approval lifecycle remains in `CAP-GOV-002`.
- Manual review confirms immutable schedule updates and recipient-only effects.
