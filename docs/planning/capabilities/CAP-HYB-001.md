---
id: CAP-HYB-001
status: ready
started: null
completed: null
adr_refs:
  - ADR-006
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
- [ ] Give persistence adapters a repository contract and contract tests for
  the one-allocation-per-contribution key, and emit hybrid audit events.
- [ ] Apply an explicit policy for late and missed contributions.
- [ ] Report dues, unpaid rotation entitlement, and units in one settlement
  position.
- [ ] Apply an explicit member-exit treatment to outstanding units.
- [ ] Derive combined reporting from shared contribution and investment-event
  provenance.

## Implementation Tasks

Policies are decided in
[ADR-006](../../architecture/adr/ADR-006-hybrid-contribution-allocation.md).
Tasks are listed in delivery order.

- [TASK-HYB-001](../tasks/TASK-HYB-001.md) - ready: versioned hybrid rules
- [TASK-HYB-002](../tasks/TASK-HYB-002.md) - ready: pot and fund split
- [TASK-HYB-003](../tasks/TASK-HYB-003.md) - ready: once-only unit issuance
- [TASK-HYB-004](../tasks/TASK-HYB-004.md) - ready: allocation reversals
- [TASK-GOV-007](../tasks/TASK-GOV-007.md) - ready: exit and waiver decisions
  with recusal
- [TASK-HYB-005](../tasks/TASK-HYB-005.md) - ready: partial payments, arrears,
  catch-up, and collateral
- [TASK-HYB-006](../tasks/TASK-HYB-006.md) - ready: member exit and entitlement
- [TASK-HYB-007](../tasks/TASK-HYB-007.md) - ready: combined settlement report
- [TASK-HYB-008](../tasks/TASK-HYB-008.md) - ready: allocation repository
  contract, adapter guidance, and audit wiring

The Kolo adapter's unique database constraint on the allocation key is built in
the adapter project against the TASK-HYB-008 contract tests.

## Verification

- Unit tests: effective-cycle split resolution, derived amounts, duplicate
  issuance, missed/late outcomes, settlement, and exit policy.
- Integration tests: end-to-end flow from public contribution record to unit
  issuance and combined member reporting.
- Manual review: ledger source-of-truth, event lineage, and no payment execution.
