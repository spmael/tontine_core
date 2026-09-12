---
id: CAP-ACCOUNT-001
status: backlog
adr_refs: []
depends_on:
  - CAP-PACKAGE-001
blocks: []
requirements:
  - FR-ACC-001
  - FR-ACC-002
  - NFR-ACC-001
owner: domain
---

# Capability: Financial Account Registry

## Outcome

The package can record where group money or assets are expected to be held and
link recorded financial events to that location without accessing or controlling
external funds.

## Domain Boundary

- Inputs: account identity, institution metadata, currency, masked reference, ledger mapping
- Outputs: registered financial account records and event references
- Invariants: credentials are never stored; account access is never initiated; currency is explicit
- Exclusions: bank connectivity, live balance synchronization, payment execution, and custody

## Acceptance Criteria

- [ ] Register cash, bank, mobile wallet, broker, and other account types.
- [ ] Record institution, country, currency, masked reference, custodian description, and active status.
- [ ] Link a registered account to a logical ledger account.
- [ ] Allow contributions, payouts, cash movements, and investments to reference the account.
- [ ] Reject credentials, unmasked secrets, and unsupported account-access operations.
- [ ] Reconstruct account references from recorded events without live external access.

## Implementation Tasks

- TASK-ACCOUNT-001: Define financial account entities and safe references.
- TASK-ACCOUNT-002: Link financial accounts to ledger and transaction records.
- TASK-ACCOUNT-003: Add account registry tests and documentation.

## Verification

- Unit tests: account validation, masking, mapping, and event references
- Boundary review: no credentials, network clients, or payment execution in the core
