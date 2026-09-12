---
id: CAP-INV-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
adr_refs:
  - ADR-003
depends_on:
  - CAP-CON-001
  - CAP-LEDGER-001
  - CAP-ACCOUNT-001
blocks: []
requirements:
  - FR-INV-001
  - FR-INV-002
  - FR-INV-003
  - FR-INV-004
  - FR-INV-005
owner: domain
---

# Capability: Investment Tontine

## Outcome

A consumer can configure investment allocations, record investment activity and
manual valuations, calculate NAV, and track deterministic member ownership
without broker access or investment execution.

## Domain Boundary

- Inputs: allocation rules, asset definitions, transactions, valuations, liabilities, units, supplied FX rates
- Outputs: investment records, asset values, NAV, unit prices, member ownership
- Invariants: percentages are explicit and valid; monetary values use Decimal; FX rates are supplied and timestamped; ownership calculations are deterministic
- Exclusions: broker connectivity, market-data retrieval, investment execution, custody, and external FX calls from the core

## Acceptance Criteria

- [x] Define configurable allocation categories and percentages.
- [x] Record cash, assets, purchases, sales, income, fees, and manual valuations.
- [x] Calculate assets, liabilities, NAV, unit price, and member ownership.
- [x] Issue and track member units deterministically.
- [x] Convert multi-currency asset values only with supplied, auditable FX rates.

## Implementation Tasks

- [x] TASK-INV-001: Define allocation, asset, valuation, and supplied FX-rate vocabulary.
- [x] TASK-INV-002: Record investment activity and manual valuations.
- [x] TASK-INV-003: Calculate NAV, unit price, and member ownership.
- [x] TASK-INV-004: Implement deterministic member-unit issuance and redemption.
- [x] TASK-INV-005: Add external FX adapter boundary and multi-currency tests.
- [x] TASK-INV-006: Automatically carry allocation rules across cycles.

## Verification

- Unit tests cover Decimal precision, allocation totals, transactions, valuations, NAV, units, and supplied FX rates.
- Boundary review confirms no broker, market-data, payment, or investment-execution client enters the core.
