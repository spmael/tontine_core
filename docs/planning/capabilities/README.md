# Capability Map

Capabilities are package-level boundaries. Each capability must trace to
requirements in [`../requirements.md`](../requirements.md), define testable
behavior, and own focused tasks once task decomposition is approved.

## Delivery Order

| ID | Capability | Requirements | Status | Delivery intent |
| --- | --- | --- | --- | --- |
| CAP-PACKAGE-001 | Package foundation | FR-PKG-001, NFR-PKG-001, NFR-SCP-001 | ready | First delivery item |
| CAP-GROUP-001 | Group and membership | FR-GRP-001..004 | ready | After package foundation |
| CAP-CON-001 | Contribution engine | FR-CON-001..006 | shipped | First vertical slice |
| CAP-ACCOUNT-001 | Financial account registry | FR-ACC-001..002, NFR-ACC-001 | backlog | Before ledger integration |
| CAP-CLASSIC-001 | Classic rotation | FR-CLS-001..004 | backlog | After contribution slice |
| CAP-LEDGER-001 | Double-entry ledger | FR-LDG-001..004, NFR-CAL-* | backlog | Shared financial foundation |
| CAP-INV-001 | Investment tracking | FR-INV-001..005 | backlog | After ledger foundation |
| CAP-GOV-001 | Governance and audit | FR-GOV-001..004 | backlog | Rules and event history |
| CAP-LOCATION-001 | Optional location metadata | FR-LOC-001..002 | shipped | After group and membership |
| CAP-REPORT-001 | Statements and reporting | FR-RPT-001..003 | backlog | After core projections |
| CAP-API-001 | Public API and adapters | FR-API-001..003 | backlog | Package boundary |

## Next-Version Gap Backlog

The following capabilities formalize proposed future scope from
[`../../TONTINE_CORE_GAPS_v1.md`](../../TONTINE_CORE_GAPS_v1.md). They are
backlog-only: task decomposition is deferred until the architecture choices in
[`../../architecture/next-version-gap-architecture.md`](../../architecture/next-version-gap-architecture.md)
are reviewed.

| ID | Capability | Requirements | Status | Planning note |
| --- | --- | --- | --- | --- |
| CAP-STATE-001 | Stateful registry contracts | FR-API-004, FR-LDG-006 | backlog | Snapshot/replay contract remains open |
| CAP-GOV-002 | Reusable governance decisions | FR-GOV-005..009, FR-GOV-011 | backlog | Approval and temporal policies remain open |
| CAP-CLASSIC-002 | Versioned rotations and exceptions | FR-CLS-005, FR-GOV-010 | backlog | Exception semantics remain open |
| CAP-CON-002 | Contribution penalty and time inputs | FR-CON-007, NFR-API-002 | backlog | Preserve strict timezone-aware inputs |
| CAP-INV-002 | Investment activity query and validation | FR-INV-006..009 | backlog | Empty valuation and currency policy remain open |
| CAP-LEDGER-002 | Point-in-time ledger projections | FR-LDG-005, NFR-PERF-001 | backlog | Preserve immutable journal source of truth |
| CAP-MEM-001 | Member shares and responsibilities | FR-MEM-001..002 | backlog | Share identity and conflict policy remain open |
| CAP-HYB-001 | Hybrid contribution allocation | FR-HYB-001..005 | backlog | Split, missed-payment, and exit rules remain open |
| CAP-API-002 | Actionable public API errors and time semantics | NFR-API-001..002 | backlog | No silent defaults or built-in lookup errors |

## First Vertical Slice

First establish the package foundation, then implement a small, in-memory,
framework-independent flow:

1. Create an importable `tontine` package under `src/`.
2. Configure `tontine-core` distribution metadata and Python 3.12+ tooling.
3. Add a package import smoke test.
4. Create a JPY tontine in draft status.
5. Add five active members.
6. Define a monthly JPY 30,000 contribution rule.
7. Create one contribution cycle.
8. Record a paid, partial, late, and missed contribution.
9. Report expected, received, and outstanding contributions.
10. Validate duplicate contribution rejection.

This slice proves the basic domain language and test shape before introducing
payouts, ledger posting, investment valuation, or governance workflows.
