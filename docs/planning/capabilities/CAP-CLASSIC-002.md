---
id: CAP-CLASSIC-002
status: backlog
started: null
completed: null
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
- Outputs: deterministic recipient order for a requested cycle
- Invariants: resolution uses the latest applicable version; historical orders
  remain unchanged; exceptions do not leak into other cycles
- Exclusions: proposal voting, randomized order generation, payment execution,
  and persistence adapters

## Acceptance Criteria

- [ ] Resolve a cycle's order from rotation versions independently of proposal
  and vote replay.
- [ ] Keep version ordering deterministic for equal or conflicting effective
  cycles.
- [ ] Represent an approved one-cycle exception without changing the base order.
- [ ] Reject invalid recipients, positions, and exception cycle scope.
- [ ] Preserve historical rotation resolution after later versions are added.

## Implementation Tasks

Task decomposition is intentionally deferred until rotation-exception semantics
are reviewed in
[`../../architecture/next-version-gap-architecture.md`](../../architecture/next-version-gap-architecture.md).

## Verification

- Unit tests: effective-cycle resolution, boundary cycles, invalid versions,
  exception application, and restoration of the base order afterward.
- Integration tests: resolution does not construct or replay a governance
  registry.
- Manual review: rotation immutability and approval-effect boundary.
