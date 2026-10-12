---
id: CAP-LEDGER-002
status: backlog
started: null
completed: null
adr_refs: []
depends_on:
  - CAP-LEDGER-001
blocks: []
requirements:
  - FR-LDG-005
  - NFR-PERF-001
owner: domain
---

# Capability: Point-in-Time Ledger Projections

## Outcome

A consumer can query deterministic account balances at the present or at an
explicit historical instant without implementing full journal replay per read.

## Domain Boundary

- Inputs: immutable posted journals, account identity, currency, optional
  timezone-aware `as_of` instant
- Outputs: balances derived from journals and reusable projections
- Invariants: journals remain the financial source of truth; as-of boundaries
  are deterministic; projections can be rebuilt
- Exclusions: bank reconciliation, external statements, mutable balance fields,
  and payment execution

## Acceptance Criteria

- [ ] Support a timezone-aware point-in-time balance query.
- [ ] Include only posted journals recorded on or before the requested instant.
- [ ] Avoid requiring application consumers to replay all journal history for
  each balance read.
- [ ] Keep any indexes or checkpoints derived from immutable journal records.
- [ ] Preserve current balance behavior when no `as_of` instant is supplied.

## Implementation Tasks

Task decomposition is intentionally deferred until the state contract and
projection boundary are reviewed.

## Verification

- Unit tests: inclusive timestamp boundary, timezone handling, corrections,
  multiple currencies, and parity with a full journal-derived calculation.
- Integration tests: repeated public balance queries and point-in-time reads.
- Manual review: derived-projection/source-of-truth boundary.
