---
id: ADR-007
status: accepted
date: 2026-10-18
---

# ADR-007: Versioned State Snapshots and Rebuildable Projections

## Context

The package has stateful in-memory registries that adapters need to persist and
restore deterministically. Governance already has a schema-versioned snapshot
under ADR-004. Hybrid allocation, arrears, exit, and member-unit state still
need a consistent restoration contract. The accounting ledger has a separate
immutable journal source of truth; any balance projection must be rebuilt from
those journals.

## Decision

- Use immutable, typed, schema-versioned snapshots as the supported state
  interchange for stateful non-ledger registries. Each registry snapshot names
  its schema version and rejects unsupported versions. The core defines values
  and restore validation, but not a serialized wire format, durable store, or
  in-core schema migration.
- Extend the governance snapshot decision in ADR-004 to the hybrid allocation,
  arrears, exit, and member-unit registries. Restored state must preserve
  append-only event and audit provenance; audit events are not replayed as a
  second canonical state source.
- Member unit balances are derived from immutable, ordered issue and redemption
  events. A unit-ledger snapshot stores those events, not cached balances, and
  rebuilds the projection by validating and applying the event sequence.
- The accounting ledger remains journal-authoritative. Its journals are the
  persisted financial history; any balance index or checkpoint is derived and
  must be rebuilt from the immutable journals. The core does not add a second
  ledger snapshot as an alternative source of truth.
- Governance proposals retain their electorate snapshot at creation. A
  membership change affects future proposals and does not rewrite eligibility
  when a snapshot is restored, as decided in ADR-004.
- Existing record-level replay helpers are not a general snapshot or event-log
  interchange contract. Persistence adapters serialize supported snapshots
  and migrate older payloads explicitly before passing them to the core.

## Alternatives Considered

- **Canonical event replay for all registries**: rejected because several
  registries do not expose a complete canonical event stream, and replaying
  public mutations would depend on historical validation context.
- **Both snapshots and replay as supported recovery paths**: rejected because
  two authoritative paths create unnecessary consistency and migration rules.
- **Persist derived unit or ledger balances separately**: rejected because
  cached balances can diverge from the immutable event or journal source.
- **A single universal snapshot structure**: rejected because registries have
  different typed state and validation invariants; a common schema envelope
  would add indirection without providing a shared domain contract.

## Consequences

### Positive

- Adapters receive deterministic restore APIs and can detect unsupported
  snapshots rather than silently loading incompatible state.
- Unit projections remain reproducible from explicit immutable events, and
  accounting-ledger projections remain reproducible from journals.
- Domain code stays independent of databases, serializers, and frameworks.

### Trade-offs

- Each registry owns and tests its schema version and restore invariants.
- Adapters must manage wire-format versioning and perform any payload migration
  outside the core.
- Snapshot support is delivered incrementally; registries without a published
  snapshot contract must not be treated as persistable through undocumented
  mutation sequences.

## Verification

- Round-trip snapshots preserve ordered source events and derived balances.
- Unsupported versions, duplicate event identifiers, invalid event order, and
  inconsistent dependent registry state are rejected.
- Ledger projections match a fresh rebuild from the immutable journal history.
