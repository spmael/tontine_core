---
id: CAP-REPORT-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
adr_refs: []
depends_on:
  - CAP-GROUP-001
  - CAP-CON-001
  - CAP-CLASSIC-001
  - CAP-INV-001
  - CAP-LEDGER-001
  - CAP-GOV-001
blocks: []
requirements:
  - FR-RPT-001
  - FR-RPT-002
  - FR-RPT-003
owner: reporting
---

# Capability: Statements and Reporting

## Outcome

A consumer can obtain deterministic structured member and group statements,
contribution status reports, and investment summaries without requiring PDF,
Excel, web, database, or rendering dependencies.

## Domain Boundary

- Inputs: members, cycles, contributions, payouts, investments, valuations, units, ledger balances, proposals, and audit events
- Outputs: immutable structured report objects and summary projections
- Invariants: report values are derived from supplied domain records; Decimal amounts and currencies remain explicit; output is deterministic
- Exclusions: PDF, Excel, HTML, web rendering, database queries, authentication, and external financial-data retrieval

## Acceptance Criteria

- [x] Expose structured member statements.
- [x] Expose structured group statements.
- [x] Expose contribution status and investment summary reports.
- [x] Preserve Decimal amounts, currencies, dates, timestamps, and provenance.
- [x] Keep presentation rendering outside the core package.

## Implementation Tasks

- [x] TASK-REPORT-001: Define structured member statements.
- [x] TASK-REPORT-002: Define structured group statements.
- [x] TASK-REPORT-003: Add contribution and investment summary projections.
- [x] TASK-REPORT-004: Add reporting tests, examples, and rendering boundary documentation.

## Verification

- Unit tests cover empty, partial, and complete member/group reporting data.
- Report output is deterministic and infrastructure-free.
- Boundary review confirms no presentation renderer or external service enters the core.
