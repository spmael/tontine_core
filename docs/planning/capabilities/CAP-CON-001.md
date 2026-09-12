---
id: CAP-CON-001
status: ready
adr_refs: []
depends_on:
  - CAP-PACKAGE-001
  - CAP-GROUP-001
blocks: []
requirements:
  - FR-CON-001
  - FR-CON-002
  - FR-CON-003
  - FR-CON-004
  - FR-CON-005
owner: domain
---

# Capability: Contribution Engine

## Outcome

A consumer can define a monthly contribution rule, create a cycle, record
contributions, and identify outstanding amounts without processing payments.

## Domain Boundary

- Inputs: contribution rule, cycle dates, member, expected and actual amounts
- Outputs: cycle and contribution entities, status reports
- Invariants: amounts are non-negative; currency matches; duplicate records are rejected
- Exclusions: payment initiation, custody, bank reconciliation, and penalties beyond configured rules

## Acceptance Criteria

- [ ] Define a monthly contribution rule with amount, currency, due date, grace period, and effective date.
- [ ] Create a cycle with expected member contributions.
- [ ] Record paid, partial, late, missed, and pending contribution states.
- [ ] Report expected, received, and outstanding amounts.
- [ ] Reject duplicate contribution records unless explicitly adjusted.

## Implementation Tasks

- TASK-CON-001: Define contribution rule and cycle value objects.
- TASK-CON-002: Implement contribution recording and status transitions.
- TASK-CON-003: Add outstanding-contribution projection and tests.
