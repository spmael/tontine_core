---
kind: requirements_register
source: BRD.md
status: active
---

# tontine-core Requirements Register

This register translates the BRD into stable, testable requirement IDs. The BRD
remains authoritative; this file provides planning and traceability.

## Package Foundation

### FR-PKG-001 - Establish the package boundary

The distribution must be named `tontine-core`, the Python import package must be
named `tontine`, and the source must use the BRD-recommended `src/tontine/`
layout with an importable public package.

### NFR-PKG-001 - Establish the development baseline

The package must target Python 3.12 or newer, use modern `pyproject.toml`
metadata, and provide an isolated test and quality-check workflow without a web
framework or database dependency.

## Financial Account Registry

### FR-ACC-001 - Register financial accounts

The package must register the external account or custody location associated
with group money or assets, including type, institution, country, currency,
masked reference, custodian description, linked ledger account, and status.

### FR-ACC-002 - Link events to financial accounts

Contributions, payouts, cash movements, and investment transactions must be able
to reference a registered financial account without initiating or processing the
underlying payment.

### NFR-ACC-001 - Keep account access outside the core

The package must not store account credentials, connect to financial institutions,
retrieve live balances, initiate transfers, or synchronize accounts automatically.

## Group and Membership

### FR-GRP-001 - Create a tontine

The package must create a tontine with an identifier, name, description, base
currency, creation date, status, ruleset reference, contribution frequency,
contribution amount, and active cycle reference.

### FR-GRP-002 - Manage membership

The package must add members with unique identifiers, display names, membership
start dates, statuses, and roles.

### FR-GRP-003 - Enforce membership transitions

The package must support invited, active, suspended, left, and removed statuses
and reject invalid transitions.

### FR-GRP-004 - Support domain roles

The package must represent member, treasurer, and administrator roles without
implementing application authentication.

### FR-LOC-001 - Support optional group jurisdiction metadata

The package may record an optional ISO 3166-1 alpha-2 jurisdiction for a group;
the field must not be required for group creation or used as a payment or
regulatory decision.

### FR-LOC-002 - Support optional member residence metadata

The package may record an optional ISO 3166-1 alpha-2 residence country for a
member without implementing identity verification, tax classification, or KYC.

## Contribution Engine

### FR-CON-001 - Define contribution rules

The package must define amount, currency, frequency, due-date convention, grace
period, optional late penalty, and effective date. Daily, weekly, and monthly
contributions are the initial supported frequencies.

### FR-CON-002 - Create contribution cycles

The package must create cycles with start date, due date, status, expected
contributions, recorded contributions, outstanding contributions, and an
associated payout or allocation.

### FR-CON-003 - Record contributions

The package must record member, cycle, expected amount, actual amount, payment
date, status, external reference, and notes without processing payment.

### FR-CON-004 - Detect contribution status

The package must identify pending, paid, partial, late, and missed contributions
and report outstanding contributions.

### FR-CON-005 - Prevent duplicate contribution records

The package must reject duplicate contribution records unless an explicit
adjustment or correction path is used.

## Classic Tontine

### FR-CLS-001 - Configure rotation

The package must define recipient order and validate that each active member has a
valid rotation position.

### FR-CLS-002 - Determine cycle recipient

The package must identify the recipient and calculate the expected payout for each
classic cycle.

### FR-CLS-003 - Record classic payout

The package must record payouts, retain historical recipient data, and prevent
duplicate payouts for a cycle.

### FR-CLS-004 - Configure unpaid-contribution policy

The package must allow governance rules to decide whether a payout can proceed
when contributions are unpaid.

## Investment Tontine

### FR-INV-001 - Configure allocation rules

The package must support configurable allocation categories and percentages
without hard-coded investment allocations.

### FR-INV-002 - Record investment activity

The package must record cash balances, asset definitions, purchases, sales,
income, fees, and manual valuation updates.

### FR-INV-003 - Calculate investment value

The package must calculate total assets, total liabilities, net asset value, and
member economic ownership.

### FR-INV-004 - Track member units

The package must use a deterministic unit-based ownership model with sufficient
precision for issuance, redemption, contributions, and distributions.

### FR-INV-005 - Support multi-currency assets

The package must record assets in currencies other than the tontine base currency;
FX rates must be supplied externally.

## Ledger and Accounting

### FR-LDG-001 - Maintain a source-of-truth ledger

Financial balances must be derived from ledger entries rather than manually
maintained balance fields.

### FR-LDG-002 - Validate double-entry transactions

Every financial event must create balanced debit and credit entries.

### FR-LDG-003 - Record journal provenance

Each journal entry must include an identifier, timestamps, description, entries,
source event, optional reference, and actor where available.

### FR-LDG-004 - Preserve posted entries

Posted ledger entries must be immutable. Corrections must use reversal or
adjustment entries.

## Governance and Audit

### FR-GOV-001 - Version group rules

Each tontine must have versioned rulesets with effective dates, and historical
events must reference the rules applicable at the time.

### FR-GOV-002 - Manage proposals

The package must create, open, approve, reject, expire, and cancel proposals with
proposer, deadline, threshold, and status data.

### FR-GOV-003 - Record votes

The package must support one-member-one-vote with yes, no, and abstain choices
and calculate whether the approval threshold is reached.

### FR-GOV-004 - Record audit events

The package must append significant financial and non-financial events such as
member changes, corrections, valuations, proposals, votes, and cycle closure.

## Statements and Reporting

### FR-RPT-001 - Generate member statements

The package must expose structured member statements containing contribution
history, outstanding amounts, penalties, payouts, units, ownership, and current
attributable value.

### FR-RPT-002 - Generate group statements

The package must expose structured group statements containing membership, cycle,
contributions, cash, investments, liabilities, NAV, payouts, and proposals.

### FR-RPT-003 - Exclude presentation rendering

The core package must expose structured reports without requiring PDF, Excel, or
web rendering.

## Persistence and Public API

### FR-API-001 - Preserve framework independence

The business domain must not require Django ORM models or another web framework.

### FR-API-002 - Expose repository boundaries

The package must expose entities and repository interfaces that can support
in-memory persistence and later SQL, Django, SQLAlchemy, or other adapters.

### FR-API-003 - Provide a readable public API

The package must provide a typed, documented API for creating tontines, recording
contributions, managing cycles, posting financial events, and generating reports.

## Non-functional Requirements

### NFR-CAL-001 - Use exact monetary arithmetic

Monetary values must use `decimal.Decimal`; binary floating-point arithmetic must
not be used for financial calculations.

### NFR-CAL-002 - Deterministic calculations

Financial calculations, ownership results, and validation outcomes must be
deterministic and reproducible.

### NFR-TEST-001 - Test without infrastructure

Core business rules must be unit-testable without a database or web framework.

### NFR-DOC-001 - Document public APIs

Every public class and function must have concise docstrings, and practical
examples must cover both tontine modes.

### NFR-SEC-001 - Keep security boundaries explicit

The package must not store secrets or bank credentials and must expose clear
interfaces for consuming applications to implement access control.

### NFR-SCP-001 - Respect Version 1 exclusions

The package must not include custody, payment initiation, broker execution,
automated FX, lending, tax calculation, KYC/AML, market-data feeds, or regulatory
reporting.

## Traceability Summary

| BRD area | Requirement IDs | Initial capability |
| --- | --- | --- |
| Package Foundation | FR-PKG-001, NFR-PKG-001 | CAP-PACKAGE-001 |
| Financial Account Registry | FR-ACC-001..002, NFR-ACC-001 | CAP-ACCOUNT-001 |
| Group and Membership | FR-GRP-001..004 | CAP-GROUP-001 |
| Contribution Engine | FR-CON-001..005 | CAP-CON-001 |
| Classic Tontine | FR-CLS-001..004 | CAP-CLASSIC-001 |
| Investment Tontine | FR-INV-001..005 | CAP-INVEST-001 |
| Ledger and Accounting | FR-LDG-001..004 | CAP-LEDGER-001 |
| Governance and Audit | FR-GOV-001..004 | CAP-GOV-001 |
| Statements and Reporting | FR-RPT-001..003 | CAP-REPORT-001 |
| Persistence and Public API | FR-API-001..003 | CAP-API-001 |
| Non-functional | NFR-CAL-001..NFR-SCP-001 | Cross-cutting |
