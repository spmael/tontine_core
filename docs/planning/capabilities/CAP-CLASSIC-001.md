---
id: CAP-CLASSIC-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
adr_refs:
  - ADR-002
depends_on:
  - CAP-GROUP-001
  - CAP-CON-001
  - CAP-LEDGER-001
blocks: []
requirements:
  - FR-CLS-001
  - FR-CLS-002
  - FR-CLS-003
  - FR-CLS-004
owner: domain
---

# Capability: Classic Tontine Rotation and Payouts

## Outcome

A consumer can configure a deterministic recipient rotation, identify the
recipient for each cycle, calculate the expected payout, and record the payout
without moving funds.

## Domain Boundary

- Inputs: active members, rotation order, cycle number, contribution amounts, unpaid-contribution policy
- Outputs: recipient selection, expected payout, recorded payout provenance
- Invariants: each active member has one rotation position; recipients are deterministic; payouts cannot duplicate a cycle
- Exclusions: payment execution, custody, bank access, and hard-coded treatment of unpaid contributions

## Acceptance Criteria

- [x] Define and validate recipient order for active members.
- [x] Identify the cycle recipient deterministically.
- [x] Calculate the expected payout from recorded contribution amounts.
- [x] Record payouts with historical recipient data and reject duplicates.
- [x] Apply an explicit configurable policy when contributions are unpaid.

## Implementation Tasks

- [x] TASK-CLASSIC-001: Define rotation order, recipient selection, and payout calculation.
- [x] TASK-CLASSIC-002: Record payouts with immutable provenance and duplicate protection.
- [x] TASK-CLASSIC-003: Add configurable unpaid-contribution policy and tests.

## Verification

- Unit tests cover rotation validity, recipient selection, Decimal payout totals, duplicate payouts, and unpaid-policy behavior.
- Boundary review confirms no payment execution or custody behavior.
