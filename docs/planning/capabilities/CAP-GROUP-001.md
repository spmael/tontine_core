---
id: CAP-GROUP-001
status: ready
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
- Invariants: identifiers are unique; status transitions are valid; roles are explicit
- Exclusions: authentication, identity verification, and persistence adapters

## Acceptance Criteria

- [ ] Create a draft tontine with a valid ISO currency code.
- [ ] Add members with unique identifiers and explicit roles.
- [ ] Reject duplicate member identifiers.
- [ ] Enforce valid membership status transitions.
- [ ] Expose deterministic, framework-independent domain behavior.

## Implementation Tasks

- TASK-GROUP-001: Define identifiers, statuses, roles, and value objects.
- TASK-GROUP-002: Implement tontine and member domain entities.
- TASK-GROUP-003: Add in-memory repository behavior and tests.
