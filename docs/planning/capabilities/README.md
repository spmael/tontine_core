# Capability Map

Capabilities are package-level boundaries. Each capability must trace to
requirements in [`../requirements.md`](../requirements.md), own focused tasks,
and expose testable behavior.

## Delivery Order

| ID | Capability | Requirements | Status | Delivery intent |
| --- | --- | --- | --- | --- |
| CAP-PACKAGE-001 | Package foundation | FR-PKG-001, NFR-PKG-001, NFR-SCP-001 | ready | First delivery item |
| CAP-GROUP-001 | Group and membership | FR-GRP-001..004 | ready | After package foundation |
| CAP-CON-001 | Contribution engine | FR-CON-001..006 | shipped | First vertical slice |
| CAP-ACCOUNT-001 | Financial account registry | FR-ACC-001..002, NFR-ACC-001 | backlog | Before ledger integration |
| CAP-CLASSIC-001 | Classic rotation | FR-CLS-001..004 | backlog | After contribution slice |
| CAP-LEDGER-001 | Double-entry ledger | FR-LDG-001..004, NFR-CAL-* | backlog | Shared financial foundation |
| CAP-INVEST-001 | Investment tracking | FR-INV-001..005 | backlog | After ledger foundation |
| CAP-GOV-001 | Governance and audit | FR-GOV-001..004 | backlog | Rules and event history |
| CAP-LOCATION-001 | Optional location metadata | FR-LOC-001..002 | shipped | After group and membership |
| CAP-REPORT-001 | Statements and reporting | FR-RPT-001..003 | backlog | After core projections |
| CAP-API-001 | Public API and adapters | FR-API-001..003 | backlog | Package boundary |

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
