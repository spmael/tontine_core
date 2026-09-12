---
id: CAP-LEDGER-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
adr_refs:
  - ADR-001
depends_on:
  - CAP-PACKAGE-001
  - CAP-GROUP-001
  - CAP-CON-001
  - CAP-ACCOUNT-001
blocks: []
requirements:
  - FR-LDG-001
  - FR-LDG-002
  - FR-LDG-003
  - FR-LDG-004
  - NFR-CAL-001
  - NFR-CAL-002
owner: domain
---

# Capability: Ledger and Accounting

## Outcome

A consumer can record balanced double-entry financial events and derive account
balances from immutable ledger entries without moving or custodying funds.

## Domain Boundary

- Inputs: logical accounts, Decimal amounts, currencies, financial events, provenance
- Outputs: journal entries, posted ledger records, derived balances, corrections
- Invariants: every posted journal balances; posted entries are immutable; balances are derived from entries
- Exclusions: payment execution, custody, bank reconciliation, market data, and external FX retrieval

## Acceptance Criteria

- [x] Define Decimal-based ledger accounts, entries, journals, and provenance.
- [x] Reject unbalanced journal entries and derive balances from posted entries.
- [x] Preserve posted entries as immutable records.
- [x] Correct posted entries only through reversals or adjustments.
- [x] Keep financial currency and precision explicit.

## Implementation Tasks

- [x] TASK-LEDGER-001: Define ledger vocabulary and journal provenance.
- [x] TASK-LEDGER-002: Implement balanced posting and derived balances.
- [x] TASK-LEDGER-003: Preserve posted entries and support corrections.

## Verification

- Unit tests cover Decimal precision, balancing, derived balances, provenance, immutability, reversals, and adjustments.
- Boundary review confirms no payment, custody, network, or live-balance behavior.
