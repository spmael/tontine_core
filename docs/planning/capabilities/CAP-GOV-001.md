---
id: CAP-GOV-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
adr_refs: []
depends_on:
  - CAP-GROUP-001
  - CAP-CLASSIC-001
blocks: []
requirements:
  - FR-GOV-001
  - FR-GOV-002
  - FR-GOV-003
  - FR-GOV-004
owner: domain
---

# Capability: Governance and Audit

## Outcome

A consumer can propose and approve group decisions, including rotation changes,
while preserving a traceable audit history.

## Domain Boundary

- Inputs: proposals, member votes, thresholds, effective dates, audit events
- Outputs: versioned decisions, approved rotation orders, audit records
- Invariants: decisions follow explicit thresholds; historical decisions remain immutable and traceable
- Exclusions: authentication, legal identity verification, external signatures, and regulatory compliance decisions

## Acceptance Criteria

- [x] Version group rules with effective dates.
- [x] Create and transition proposals.
- [x] Record one-member-one-vote decisions and approval thresholds.
- [x] Approve rotation changes without mutating historical rotations.
- [x] Preserve significant governance and financial audit events.

## Implementation Tasks

- [x] TASK-GOV-001: Add vote-approved rotation proposals and governance primitives.
- [x] TASK-GOV-002: Add cross-capability append-only audit event registry.

## Verification

- Unit tests cover proposal lifecycle, vote thresholds, effective dates, rotation history, and audit events.
- Boundary review confirms no authentication or external signature system is introduced.
