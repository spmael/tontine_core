---
id: CAP-LEDGER-002
status: shipped
started: 2026-10-21
completed: 2026-10-21
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

- [x] Support a timezone-aware point-in-time balance query.
- [x] Include only posted journals recorded on or before the requested instant.
- [x] Avoid requiring application consumers to replay all journal history for
  each balance read.
- [x] Keep any indexes or checkpoints derived from immutable journal records.
- [x] Preserve current balance behavior when no `as_of` instant is supplied.

## Implementation Tasks

- [TASK-LEDGER-004](../tasks/TASK-LEDGER-004.md) - shipped: indexed
  point-in-time account balances

## Verification

- Unit tests: inclusive timestamp boundary, timezone handling, corrections,
  multiple currencies, and parity with a full journal-derived calculation.
- Integration tests: repeated public balance queries and point-in-time reads.
- Manual review: derived-projection/source-of-truth boundary.
