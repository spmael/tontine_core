---
id: CAP-CON-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
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
  - FR-CON-006
owner: domain
---

# Capability: Contribution Engine

## Outcome

A consumer can define a daily, weekly, or monthly contribution rule, create a cycle, record
contributions, and identify outstanding amounts without processing payments.

## Domain Boundary

- Inputs: contribution rule, cycle dates, timezone, member, expected and actual amounts
- Outputs: cycle and contribution entities, status reports
- Invariants: amounts are non-negative; timezone-aware timestamps use the cycle timezone; duplicate records are rejected; payout/allocation association is not modeled
- Exclusions: payment initiation, custody, bank reconciliation, and penalties beyond configured rules

## Acceptance Criteria

- [x] Define a daily, weekly, or monthly contribution rule with amount, currency, due date, grace period, and effective date.
- [x] Create a cycle with expected member contributions.
- [x] Record paid, partial, late, missed, and pending contribution states.
- [x] Report expected, received, and outstanding amounts.
- [x] Reject duplicate contribution records unless explicitly adjusted.
- [x] Assess separate fixed penalties after the configured grace period and route them to the common reserve by default.

## Implementation Tasks

- [x] TASK-CON-001: Define contribution rule and cycle value objects.
- [x] TASK-CON-002: Implement contribution recording and status transitions.
- [x] TASK-CON-003: Add outstanding-contribution projection and tests.
