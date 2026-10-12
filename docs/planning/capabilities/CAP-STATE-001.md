---
id: CAP-STATE-001
status: backlog
started: null
completed: null
adr_refs: []
depends_on:
  - CAP-API-001
  - CAP-LEDGER-001
blocks: []
requirements:
  - FR-API-004
  - FR-LDG-006
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

- [ ] Define the supported state interchange contract and compatibility rules.
- [ ] Restore registries without replaying undocumented public mutations.
- [ ] Ensure membership changes do not silently corrupt restored proposal state.
- [ ] Ensure any derived ledger balance state can be rebuilt from journals.
- [ ] Keep persistence adapters outside `src/tontine/`.

## Implementation Tasks

Task decomposition is intentionally deferred until the architecture choices in
[`../../architecture/next-version-gap-architecture.md`](../../architecture/next-version-gap-architecture.md)
are reviewed.

## Verification

- Unit tests: deterministic round-trip or replay tests for each stateful registry.
- Integration tests: persistence adapters are outside the core and not yet
  included in this capability.
- Manual review: state-version compatibility, source-of-truth, and adapter-boundary
  review.
