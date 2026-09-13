---
id: CAP-GROUP-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
adr_refs: []
depends_on:
  - CAP-PACKAGE-001
blocks:
  - CAP-CON-001
requirements:
  - FR-GRP-001
  - FR-GRP-002
  - FR-GRP-003
  - FR-GRP-004
owner: domain
---

# Capability: Group and Membership

## Outcome

A consumer can create a tontine and manage its members through explicit,
validated domain operations.

## Domain Boundary

- Inputs: group identity, base currency, member identity, role, status
- Outputs: tontine and member entities
- Invariants: identifiers are unique; status transitions are valid; roles and membership start dates are explicit
- Exclusions: authentication, identity verification, and persistence adapters

## Acceptance Criteria

- [x] Create a draft tontine with a valid ISO currency code.
- [x] Add members with unique identifiers and explicit roles.
- [x] Record an explicit membership start date for each member.
- [x] Reject duplicate member identifiers.
- [x] Enforce valid membership status transitions.
- [x] Expose deterministic, framework-independent domain behavior.

## Implementation Tasks

- [x] TASK-GROUP-001: Define identifiers, statuses, roles, and value objects.
- [x] TASK-GROUP-002: Implement tontine and member domain entities.
- [x] TASK-GROUP-003: Add in-memory repository behavior and tests.
