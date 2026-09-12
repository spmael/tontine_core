---
id: CAP-API-001
status: backlog
adr_refs: []
depends_on:
  - CAP-GROUP-001
  - CAP-CON-001
  - CAP-ACCOUNT-001
  - CAP-LEDGER-001
  - CAP-CLASSIC-001
  - CAP-INV-001
blocks: []
requirements:
  - FR-API-001
  - FR-API-002
  - FR-API-003
owner: package-boundary
---

# Capability: Persistence and Public API Boundaries

## Outcome

The package exposes typed, documented repository protocols and readable public
APIs while keeping domain code independent from databases, web frameworks, and
external services.

## Domain Boundary

- Inputs: domain entities and repository operations
- Outputs: protocols, in-memory implementations, contract tests, and public entry points
- Invariants: domain code depends on protocols, adapters remain outside the core, operations are deterministic
- Exclusions: Django/SQLAlchemy implementations, HTTP APIs, authentication, network clients, and external persistence in the core

## Acceptance Criteria

- [ ] Define small repository protocols by aggregate boundary.
- [ ] Provide in-memory implementations for core repository protocols.
- [ ] Define missing-ID, duplicate-ID, ordering, immutability, and error semantics.
- [ ] Run shared contract tests against in-memory implementations.
- [ ] Expose typed and documented public API entry points.
- [ ] Keep database, web-framework, authentication, and network adapters outside the domain package.

## Implementation Tasks

- TASK-API-001: Define repository protocols and in-memory contract implementations.
- TASK-API-002: Define readable public API entry points and documentation examples.

## Verification

- Unit and contract tests run without a database or web framework.
- Boundary review confirms adapters do not leak into `src/tontine/`.
