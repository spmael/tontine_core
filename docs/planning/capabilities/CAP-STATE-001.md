---
id: CAP-STATE-001
status: in_progress
started: 2026-10-18
completed: null
adr_refs:
  - ADR-004
  - ADR-007
depends_on:
  - CAP-API-001
  - CAP-LEDGER-001
blocks: []
requirements:
  - FR-API-004
  - FR-LDG-006
  - NFR-PERF-001
owner: package-boundary
---

# Capability: Stateful Registry Contracts

## Outcome

A consumer can persist and restore stateful domain registries through a
documented, deterministic contract without depending on undocumented mutation
replay or making cached state a competing source of truth.

## Domain Boundary

- Inputs: registry state, canonical domain events, immutable ledger journals
- Outputs: documented state export/restore or replay contracts and derived
  ledger projections
- Invariants: state restoration is deterministic; derived ledger state remains
  rebuildable from immutable journals; domain code stays storage-independent
- Exclusions: database implementations, framework adapters, external event
  brokers, and mutable balances as a source of truth

## Acceptance Criteria

- [x] Define the supported state interchange contract and compatibility rules.
- [ ] Restore registries without replaying undocumented public mutations.
- [x] Ensure membership changes do not silently corrupt restored proposal state.
- [ ] Ensure any derived ledger balance state can be rebuilt from journals.
- [ ] Avoid rescanning complete journal history for each current balance read.
- [ ] Keep persistence adapters outside `src/tontine/`.

## Implementation Tasks

The state interchange contract is decided in
[ADR-007](../../architecture/adr/ADR-007-state-interchange-contract.md), with
governance snapshots and frozen proposal electorates governed by
[ADR-004](../../architecture/adr/ADR-004-governance-decision-lifecycle.md).
Tasks are listed in delivery order.

- [TASK-STATE-001](../tasks/TASK-STATE-001.md) - shipped: member-unit event
  snapshots and deterministic rebuild
- [TASK-STATE-002](../tasks/TASK-STATE-002.md) - shipped: hybrid allocation
  registry snapshots
- [TASK-STATE-003](../tasks/TASK-STATE-003.md) - shipped: hybrid arrears snapshots
- [TASK-STATE-004](../tasks/TASK-STATE-004.md) - shipped: hybrid exit snapshots
- [TASK-STATE-005](../tasks/TASK-STATE-005.md) - ready: rebuildable ledger
  balance projection

Governance snapshots are shipped by TASK-GOV-005. Point-in-time balance reads
remain in CAP-LEDGER-002.

## Verification

- Unit tests: deterministic round-trip or replay tests for each stateful registry.
- Integration tests: persistence adapters are outside the core and not yet
  included in this capability.
- Manual review: state-version compatibility, source-of-truth, and adapter-boundary
  review.
