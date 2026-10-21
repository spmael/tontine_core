# Capability Map

Capabilities are package-level boundaries. Each capability must trace to
requirements in [`../requirements.md`](../requirements.md), define testable
behavior, and own focused tasks once task decomposition is approved.

## Capability Delivery Record

| ID | Capability | Requirements | Status | Delivery record |
| --- | --- | --- | --- | --- |
| CAP-PACKAGE-001 | Package foundation | FR-PKG-001, NFR-PKG-001, NFR-SCP-001 | shipped | Initial package and tooling foundation |
| CAP-GROUP-001 | Group and membership | FR-GRP-001..004 | shipped | Group and member domain |
| CAP-CON-001 | Contribution engine | FR-CON-001..006 | shipped | Contribution rules and cycles |
| CAP-ACCOUNT-001 | Financial account registry | FR-ACC-001..002, NFR-ACC-001 | shipped | In-memory account registry |
| CAP-CLASSIC-001 | Classic rotation | FR-CLS-001..004 | shipped | Classic rotation and payout primitives |
| CAP-LEDGER-001 | Double-entry ledger | FR-LDG-001..004, NFR-CAL-* | shipped | Immutable journal and derived balances |
| CAP-INV-001 | Investment tracking | FR-INV-001..005 | shipped | Investment and ownership tracking |
| CAP-GOV-001 | Governance and audit | FR-GOV-001..004 | shipped | Governance lifecycle and audit |
| CAP-LOCATION-001 | Optional location metadata | FR-LOC-001..002 | shipped | Optional location metadata |
| CAP-REPORT-001 | Statements and reporting | FR-RPT-001..003 | shipped | Structured statements and projections |
| CAP-API-001 | Public API and adapters | FR-API-001..003 | shipped | Public package boundary |

## Extended Capability Delivery

These capabilities were identified from
[`../../TONTINE_CORE_GAPS_v1.md`](../../TONTINE_CORE_GAPS_v1.md) and planned as
extended scope. Their statuses below reflect the authoritative capability and
task records; all are now shipped. Architecture decisions are recorded in the
linked ADRs and the gap architecture note
([`../../architecture/next-version-gap-architecture.md`](../../architecture/next-version-gap-architecture.md)).

| ID | Capability | Requirements | Status | Planning note |
| --- | --- | --- | --- | --- |
| CAP-STATE-001 | Stateful registry contracts | FR-API-004, FR-LDG-006, NFR-PERF-001 | shipped | Versioned non-ledger snapshots; journal-derived projections |
| CAP-GOV-002 | Reusable governance decisions | FR-GOV-005..009, FR-GOV-011 | shipped | Explicit electorate, time, quorum, and decision effects |
| CAP-CLASSIC-002 | Versioned rotations and exceptions | FR-CLS-005, FR-GOV-010 | shipped | Immutable effective-cycle versions and scoped exceptions |
| CAP-CON-002 | Contribution penalty and time inputs | FR-CON-007, NFR-API-002 | shipped | Explicit penalty destinations and timezone-aware inputs |
| CAP-INV-002 | Investment activity query and validation | FR-INV-006..009 | shipped | Validated activity queries, explicit FX and empty-valuation policy |
| CAP-LEDGER-002 | Point-in-time ledger projections | FR-LDG-005, NFR-PERF-001 | shipped | Indexed historical reads from immutable journals |
| CAP-MEM-001 | Member shares and responsibilities | FR-MEM-001..002 | shipped | Stable cycle-effective shares and configurable conflict findings |
| CAP-HYB-001 | Hybrid contribution allocation | FR-HYB-001..005 | shipped | Versioned rules, allocation, arrears, exits, and settlement |
| CAP-API-002 | Actionable public API errors and time semantics | NFR-API-001..002 | shipped | Domain errors and explicit timestamp semantics |

## First Vertical Slice (Delivered)

The initial delivery sequence established a small, in-memory,
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

This was the initial proof of the basic domain language and test shape. Rotation,
ledger, investment valuation, governance, and related capabilities were
subsequently delivered as listed above.

## Current Planning State

The generated [`../STATUS.md`](../STATUS.md) reports 87 shipped planning items
and no backlog, ready, blocked, partial, or in-progress items. No next
implementation task is currently approved; future work should begin with a
BRD-aligned requirement and capability/task planning rather than extending this
completed delivery list speculatively.
