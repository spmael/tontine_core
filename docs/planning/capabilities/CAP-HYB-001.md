---
id: CAP-HYB-001
status: backlog
started: null
completed: null
adr_refs: []
depends_on:
  - CAP-CON-001
  - CAP-CLASSIC-001
  - CAP-INV-001
  - CAP-REPORT-001
blocks: []
requirements:
  - FR-HYB-001
  - FR-HYB-002
  - FR-HYB-003
  - FR-HYB-004
  - FR-HYB-005
owner: domain
---

# Capability: Hybrid Contribution Allocation

## Outcome

A hybrid tontine can connect contribution events to rotation and investment
positions through explicit, effective-cycle rules and produce a combined
member settlement view without duplicating financial state.

## Domain Boundary

- Inputs: recorded contributions, split rules, rotation entitlements, investment
  valuations, unit events, and membership/participation status
- Outputs: contribution allocations, idempotent unit issuance, combined
  settlement positions, and shared-event reporting projections
- Invariants: source contribution amounts and identifiers are preserved;
  investment units derive from recorded contributions; missed/late and exit
  outcomes are explicit; financial values remain ledger/event-derived
- Exclusions: payment settlement, custody, investment execution, implicit
  valuation, and application persistence

## Acceptance Criteria

- [ ] Version contribution split rules and resolve them by effective cycle.
- [ ] Derive the investment share and unit issuance from a recorded contribution
  and applicable valuation.
- [ ] Prevent duplicate issuance for a contribution.
- [ ] Apply an explicit policy for late and missed contributions.
- [ ] Report dues, unpaid rotation entitlement, and units in one settlement
  position.
- [ ] Apply an explicit member-exit treatment to outstanding units.
- [ ] Derive combined reporting from shared contribution and investment-event
  provenance.

## Implementation Tasks

Task decomposition is intentionally deferred until split, late/missed
contribution, and exit policies are reviewed in
[`../../architecture/next-version-gap-architecture.md`](../../architecture/next-version-gap-architecture.md).

## Verification

- Unit tests: effective-cycle split resolution, derived amounts, duplicate
  issuance, missed/late outcomes, settlement, and exit policy.
- Integration tests: end-to-end flow from public contribution record to unit
  issuance and combined member reporting.
- Manual review: ledger source-of-truth, event lineage, and no payment execution.
