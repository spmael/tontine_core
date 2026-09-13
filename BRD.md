# Business Requirements Document

## Project

**Name:** tontine-core

**Distribution name:** `tontine-core`

**Python import name:** `tontine`

**Document status:** Current implementation baseline

**Package version:** `0.1.0`

## 1. Purpose

`tontine-core` is a framework-independent Python library that provides domain
primitives for recording and reporting community tontine activity. The current
implementation focuses on transparent validation, deterministic calculations,
auditable records, and explicit boundaries around external money movement.

This document describes the behavior currently implemented in the repository. It
is not a product roadmap and does not define unimplemented future capabilities.

## 2. Current Users and Use

The package is intended for Python developers building applications for:

- rotating savings groups;
- classic tontines;
- community investment groups;
- investment clubs; and
- other rule-driven savings communities.

The package is a library, not an end-user application. It does not provide a web
interface, authentication system, database integration, payment integration, or
financial-institution connection.

## 3. Current Scope

The implementation currently provides the following domain capabilities:

- group creation and group identity validation;
- member identity, roles, and membership lifecycle transitions;
- contribution rules and contribution cycles;
- expected, received, pending, partial, late, and missed contributions;
- classic rotation recipient selection and payout calculation;
- classic payout records and duplicate-payout prevention;
- unpaid-contribution payout policy evaluation;
- financial-account records with masked references and custody metadata;
- account-event references and logical ledger-account links;
- double-entry ledger entries and balanced journal posting;
- immutable ledger records with reversal and adjustment support;
- investment allocation rules and effective-cycle schedules;
- investment asset definitions and manual valuations;
- investment activity records for purchases, sales, income, and fees;
- member unit issuance, redemption, and balance derivation;
- investment NAV, unit-price, and member-value calculations;
- externally supplied FX-rate records and freshness checks;
- governance rulesets, rotation proposals, votes, and approval evaluation;
- append-only audit events;
- structured member and group statements;
- typed repository protocols and deterministic in-memory repositories.

## 4. Public Package Boundary

The package uses a `src/` layout and supports Python 3.12 or newer.

The public top-level helpers are:

- `tontine.create_group(...)` for creating a draft group;
- `tontine.create_contribution_cycle(...)` for creating a contribution cycle;
- `tontine.__version__` for the package version.

Capability-specific public classes are exposed from their respective modules:

- `tontine.groups` and `tontine.members`;
- `tontine.contributions`;
- `tontine.classic`;
- `tontine.accounts`;
- `tontine.ledger`;
- `tontine.investments`;
- `tontine.governance`;
- `tontine.audit`;
- `tontine.reporting`; and
- `tontine.repositories`.

Public APIs use explicit identifiers, currency codes, dates, timezone-aware
datetimes where required, and `decimal.Decimal` for financial amounts.

## 5. Domain Requirements

### 5.1 Groups and members

A group requires a non-empty identifier, a non-blank name, and a valid ISO 4217
base currency. Group identifiers cannot contain whitespace.

Members require a non-empty identifier, a non-blank display name, and an explicit
role. Member identifiers cannot contain whitespace. Supported roles are member,
treasurer, and administrator.

Supported membership states are invited, active, suspended, left, and removed.
Invalid state transitions are rejected with domain errors.

### 5.2 Contributions and cycles

Contribution rules support daily, weekly, and monthly frequencies. Rules validate
currency, amount, due-date convention, grace period, due day, optional late
penalty, effective date, and IANA timezone.

Contribution cycles validate their identifier and timezone and maintain expected
and recorded contributions. Contribution status is derived from expected amount,
actual amount, payment date, cycle due date, and the cycle timezone.

Duplicate contribution records are rejected unless an explicit adjustment is
requested. Payment processing is outside the package.

### 5.3 Classic rotation and payouts

A classic rotation contains an ordered, unique, non-empty set of active member
identifiers. Cycle recipient selection is deterministic and wraps after the last
member. Expected payout is the exact `Decimal` sum of member contributions.

Payout records require a positive cycle number, recipient, non-negative amount,
valid currency, timezone-aware timestamp, and source event. Duplicate payouts for
a cycle are rejected. The unpaid-contribution policy supports explicit allow and
deny behavior.

### 5.4 Accounts and custody boundary

Financial accounts record external custody context, including account type,
institution, country, currency, masked reference, custodian description, and
active status.

Account references must be masked and must not contain credentials, tokens,
secrets, or long unmasked digit sequences. The package does not store account
credentials, retrieve balances, initiate payments, or move real funds.

### 5.5 Ledger

Ledger journals require immutable, timezone-aware records with source-event
provenance. A journal must contain debit and credit entries, use one currency,
and balance exactly.

Balances are derived from posted entries. Posted journals cannot be modified.
Corrections are represented by reversal or adjustment journals linked to an
existing journal.

### 5.6 Investments and ownership

Allocation rules contain named categories whose non-negative percentages total
exactly 100. Scheduled rules can be bounded, replaced, or cancelled by effective
cycle.

Investment assets and activities use explicit currencies and manually supplied
provenance. Supported activity categories are purchase, sale, income, and fee.
Manual valuations require a non-negative value, effective date, and source.

Member unit balances are derived from issue and redemption events. Unit prices
must be positive for issuance, redemption cannot exceed a member balance, and
duplicate unit event identifiers are rejected.

Investment valuation derives:

```text
NAV = assets - liabilities
unit price = NAV / units outstanding
member value = member units * unit price
```

FX rates are supplied data. The package validates currency pairs, positive rates,
timezone-aware timestamps, sources, and caller-provided freshness policies. It
does not retrieve market prices or FX rates automatically.

### 5.7 Governance and audit

Rulesets are immutable versions with positive versions and effective cycles.
Rotation proposals validate eligible proposers, candidate member order, approval
thresholds, cycle numbers, and timezone-aware dates.

Governance supports draft and open proposals, one-member-one-vote choices of yes,
no, and abstain, duplicate-vote prevention, threshold evaluation, and effective
rotation selection. Governance actions are recorded in an append-only audit
registry.

Audit events require identifiers, aggregate information, and timezone-aware
occurrence times. Event details are preserved as read-only mappings.

### 5.8 Reporting

Member statements expose structured contribution history, payouts, investment
summaries, penalties, and outstanding contribution totals.

Group statements expose active members, current cycle, expected and received
contributions, cash, investment value, liabilities, historical payouts, pending
proposals, outstanding contributions, and NAV.

Reporting objects do not render PDF, Excel, HTML, or web pages. Presentation is
the responsibility of the consuming application.

## 6. Persistence and Integration Boundary

The core package includes typed repository protocols and in-memory repository
implementations for groups, accounts, cycles, members, classic records,
governance records, audit events, and ledger records.

Database, web-framework, authentication, payment-provider, broker, market-data,
and external synchronization adapters are outside the current implementation.
The domain package must remain usable without a database, network, or web
framework.

## 7. Security and Regulatory Boundary

The package must not store secrets or financial-institution credentials. It must
not initiate payments, hold funds, execute investments, provide custody, perform
KYC or AML, calculate taxes, provide regulatory reporting, or represent itself as
a bank, broker, insurer, remittance provider, or regulated investment fund.

Consumers are responsible for application authentication, authorization,
privacy, legal review, and regulatory obligations in their jurisdictions.

## 8. Quality and Delivery Requirements

The repository uses `pyproject.toml`, setuptools as the build backend, and `uv`
for environment management and builds.

Required local checks are:

```bash
uv sync --locked
uv run pytest --cov=tontine --cov-report=term-missing
uv run ruff check src tests
uv run mypy src
uv build
```

The test suite must cover public behavior, invalid transitions, duplicate events,
financial invariants, currency handling, and precision-sensitive calculations.
The current baseline is 112 passing tests and 98% measured line coverage.

Continuous integration runs on pushes and pull requests targeting `main` using
Python 3.12 and 3.13. Release publication is triggered by a published GitHub
Release whose tag matches the package version. PyPI publication uses GitHub OIDC
Trusted Publishing and the `pypi` environment.

## 9. Explicit Non-Goals of This Baseline

The current implementation does not promise:

- a single aggregate `Tontine` application service;
- a database or durable persistence implementation;
- serialization formats;
- authentication or application permissions;
- payment processing or account synchronization;
- automatic investment execution or market-data integration;
- automatic FX conversion;
- PDF, Excel, HTML, or web rendering;
- lending, insurance, tokenization, blockchain, cryptocurrency, or fundraising.

Capabilities not described as implemented in this document should be treated as
outside the current package baseline.
