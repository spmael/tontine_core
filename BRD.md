# Business Requirements Document

## Project

**Name:** tontine-core

**Distribution name:** `tontine-core`

**Python import name:** `tontine`

**Document status:** Current implementation baseline

**Package version:** `0.2.0`

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
- reproducible classic rotation generation with immutable randomization provenance;
- effective-cycle classic rotation versions and approved one-cycle recipient overrides;
- classic payout records and duplicate-payout prevention;
- unpaid-contribution payout policy evaluation;
- financial-account records with masked references and custody metadata;
- account-event references and logical ledger-account links;
- double-entry ledger entries and balanced journal posting;
- immutable ledger records with reversal and adjustment support;
- investment allocation rules and effective-cycle schedules;
- immutable hybrid contribution policies and effective-cycle schedules;
- pure hybrid contribution split calculations using recorded amounts received;
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
- `tontine.create_contribution_cycle(...)` for creating a contribution cycle,
  optionally applying an effective contribution rule's penalty settings;
- `tontine.__version__` for the package version.

Capability-specific public classes are exposed from their respective modules:

- `tontine.groups` and `tontine.members`;
- `tontine.contributions`;
- `tontine.classic`;
- `tontine.accounts`;
- `tontine.ledger`;
- `tontine.investments`;
- `tontine.hybrid`;
- `tontine.governance`;
- `tontine.audit`;
- `tontine.reporting`; and
- `tontine.repositories`.

Public APIs use explicit identifiers, currency codes, dates, timezone-aware
datetimes where required, and `decimal.Decimal` for financial amounts.

## 5. Domain Requirements

### 5.1 Groups and members

A group requires a non-empty identifier, a non-blank name, and a valid ISO 4217
base currency. Group identifiers cannot contain whitespace. An optional group
jurisdiction may be recorded as a validated ISO 3166-1 alpha-2 country code.

Members require a non-empty identifier, a non-blank display name, and an explicit
role. Member identifiers cannot contain whitespace. Supported roles are member,
treasurer, and administrator. Each member also records an explicit membership
start date. An optional residence country may be recorded as a validated ISO
3166-1 alpha-2 country code. These fields are metadata only and do not perform
identity verification, tax classification, or regulatory decisions.

Supported membership states are invited, active, suspended, left, and removed.
Invalid state transitions are rejected with domain errors.

### 5.2 Contributions and cycles

Contribution rules support daily, weekly, and monthly frequencies. Rules validate
currency, amount, due-date convention, grace period, due day, optional late
penalty and its destination, effective date, and IANA timezone. The penalty
destination defaults to `COMMON_RESERVE`.

Contribution cycles validate their identifier and timezone and maintain expected
and recorded contributions. Contribution status is derived from expected amount,
actual amount, payment date, cycle due date, and the cycle timezone. A cycle does
not currently attach a payout or allocation record. A configured fixed penalty is
assessed after the due date plus the configured grace period for late or missed
contributions.

Cycles created with an effective rule carry its penalty amount, currency, grace
period, and destination into assessments. Duplicate contribution records are
rejected unless an explicit adjustment is requested. Penalties are separate
from contribution amounts and do not increase
contribution totals or investment units. Each assessment records its member,
cycle, reason, amount, timezone-aware assessment time, unpaid status, and
destination. `COMMON_RESERVE` remains the default when a cycle is created
without a rule. Payment processing, penalty settlement, waivers, and ledger
posting for penalties are outside the
current package behavior.

### 5.3 Classic rotation and payouts

A classic rotation contains an ordered, unique, non-empty set of active member
identifiers. Cycle recipient selection is deterministic and wraps after the last
member. Expected payout is the exact `Decimal` sum of member contributions.

A rotation may be generated from an active-member set and explicit seed. The
immutable rotation retains the seed, algorithm version, canonical input member
set, generated order, initiating actor, and timezone-aware occurrence time so
adapters can persist and later verify its provenance. Recipient lookup uses the
recorded order and does not randomize again.

Rotation schedules contain immutable versions with positive version numbers and
effective cycles. The latest effective cycle applies; the highest version number
breaks a tie at the same effective cycle. Adding a version returns a new schedule,
so existing schedule instances and earlier effective-cycle resolutions remain
unchanged.

An approved one-cycle exception overrides only the selected recipient for that
cycle. The recipient must belong to the effective rotation. The exception does
not shift later recipients, change the base rotation, alter the expected payout,
or change unpaid-contribution eligibility. It records its proposal and approval
event references and an aware approval time. The schedule consumes this approved
effect without replaying governance proposals or votes; proposal creation and
approval remain governance behavior. No durable persistence is provided by the
core package.

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

Investment assets use explicit currencies. Investment activities, manual
valuations, and liabilities include manually supplied provenance. Supported
activity categories are purchase, sale, income, and fee. Manual valuations and
liabilities require non-negative values, effective dates, and sources.

Activity in the asset currency is recorded directly. Activity in another
currency requires a supplied FX rate for exactly that currency pair; the record
keeps the original amount, the rate and its source, and the unrounded
asset-currency amount. Recorded activity can be queried by asset, type, and
inclusive effective-date bounds in effective-date, recorded-time, and event-ID
order. Purchases and sales may reference an approved governance decision that
authorizes that asset and activity type up to a cumulative maximum in the asset
currency. Activity amounts are strictly positive, recorded gross of tax or
rebates, and at least one smallest ISO 4217 unit of both the activity and asset
currencies; smaller amounts are rejected rather than rounded (ADR-005).
Purchases and sales also record a strictly positive asset quantity (`units`);
income and fees carry none. Waivers,
corrections, and unit-only corporate actions are not recorded as activity.

Member unit balances are maintained by issue and redemption operations. Unit
distributions are not currently modeled. The unit ledger calculates each
member's ownership percentage from their balance divided by total outstanding
units. Unit prices must be positive for issuance, redemption cannot exceed a
member balance, and duplicate unit event identifiers are rejected.

Investment valuation accepts caller-supplied asset and unit totals, or a
liability registry for currency-matched liability aggregation, and derives:

```text
NAV = assets - liabilities
unit price = NAV / units outstanding
member value = member units * unit price
ownership percentage = member units / total units * 100
```

Zero units outstanding is valid before the first issuance: NAV is still
derived, while unit price, member value, and ownership percentage are `None`.

Liability registries reject duplicate identifiers and aggregate recorded
liabilities by currency. Asset and investment-activity aggregation remains the
responsibility of the caller; the current package does not derive total assets
from activity records.

FX rates are supplied data. The package validates currency pairs, positive rates,
timezone-aware timestamps, sources, and caller-provided freshness policies. It
does not retrieve market prices or FX rates automatically.

### 5.7 Governance and audit

Rulesets are immutable versions with positive versions and effective cycles.
Governance can propose and approve a ruleset activation or a classic rotation
change, including a one-cycle recipient override that leaves the base rotation
available for payout and unpaid-contribution policy calculations.
Ruleset activation does not attach ruleset identifiers to historical financial
events.

Proposals freeze their eligible electorate at creation and require explicit
current-cycle context. Cycle-effective rule and rotation changes apply only
after the current cycle; member exits, penalty waivers, and payout deferrals are
decisions for the current cycle. An exit decision records its request cycle.
Approval uses yes votes divided by the frozen electorate and a two-thirds quorum
rounded up to a whole voter. Yes, no, and abstain votes count toward quorum;
abstentions do not count as yes votes. A zero quorum remains available for
threshold-only policy. A vote at the deadline is accepted and later votes are
rejected. Early evaluation is permitted only after all eligible members have
voted; otherwise evaluation waits until the deadline. Proposal effects are
applied only on approval. An expulsion subject and the member whose penalty is
being waived are excluded from the respective frozen electorate.

Governance mutations require caller-supplied timezone-aware occurrence times.
The registry supports immutable schema-versioned snapshots and deterministic
rehydration; audit events preserve provenance but are not replayed as the
canonical state source. Serialization formats and persistence adapters remain
outside the core. Approval evaluation produces approved or rejected status;
expire and cancel transitions are not currently implemented. Governance actions
are recorded in an append-only audit registry.

Audit events require identifiers, aggregate information, and timezone-aware
occurrence times. Event details are preserved as read-only mappings.

### 5.8 Reporting

Member statements expose structured contribution history, payouts, investment
summaries, penalties, and outstanding contribution totals. Penalties may be
derived from contribution summaries and remain separate from contributions.
Hybrid statements may also include a pure settlement position derived from
recorded contribution cycles, allocations, arrears, payouts, and exits. The
rotation-pot position is presented before member units, which are labelled
"member funds: redeemable" and shown as a liability unless the recorded statutes
give the group an unconditional right to refuse redemption.

Group statements expose active members, current cycle, expected and received
contributions, cash, investment value, liabilities, historical payouts, pending
proposals, penalties, outstanding contributions, and NAV.

Reporting objects do not render PDF, Excel, HTML, or web pages. Presentation is
the responsibility of the consuming application.

### 5.9 Hybrid rule policies

Hybrid rule schedules belong to an explicit group identifier. Their immutable
versions record fund-share basis points, partial-payment orders, catch-up
settings, exit-fee percentages, launch price and currency, maximum valuation age,
declared legal form, statute flags, and payout-deferral settings.

The latest effective cycle applies, with the highest version breaking a tie.
Adding a version requires a caller-supplied current cycle and rejects retroactive
activation. Cycle zero represents setup. A changed fee requires a complete
intervening cycle between adoption and activation. Each version can record a
governance decision reference, without interpreting approval.

The pure contribution split uses the amount received: it rounds the fund share
down to the currency's smallest ISO 4217 unit and assigns the exact remainder
to the rotation pot. Expected amounts are used only to measure arrears and are
not posted. Recorded contributions can be allocated once. The first allocation
uses the launch unit price while no units are outstanding; otherwise allocation
uses the latest fresh valuation on or before the pricing date. Without such a
valuation, the fund share remains pending until it can be priced without
backdating. Issued units round down to four decimal places, and the residual
remains as fund cash. An allocation reversal is a linked append-only event that
offsets the original pot, fund, units, and residual at the stored unit price;
the original allocation is never changed.

Cycle closure records unpaid rotation, fund, and penalty amounts as arrears.
Recorded receipts are applied in the effective penalty and contribution order;
the rule version and each amount are preserved. A missed contribution issues no
units. Catch-up is governed by an explicit member election before the group's
deadline, is priced at the receipt-date valuation, and remains pending if no
usable valuation exists. The deadline default forfeits only the unpaid fund
share; rotation arrears remain due. Penalty waivers require an approved
governance decision. Redemption is blocked while rotation arrears remain, and
unit offsets require an explicit valuation and event. These records do not
initiate payment or transfer funds. Approved exits freeze new allocations and
produce forward-priced entitlements, explicit arrears offsets, and payout
statuses without executing payments. A pure settlement projection combines
recorded dues, pot contributions and payouts, unit balances and values, pending
allocations and exits, elections, and offsets for member reporting.

Fees use one schedule for all units, with death fixed at zero. Cooperative
expulsion fees cannot exceed voluntary-exit fees; other declared forms receive
an explicit warning. Default payout settings cannot authorize more than 12
months; a later exit-specific, reasoned governance extension is bounded by the
24-month ceiling. Governance supports typed exit, waiver, and payout-deferral
decisions. Hybrid arrears processing, member exit entitlements, and combined
settlement reporting are implemented; the report derives unit liability
presentation from recorded statute flags and keeps the rotation pot ahead of
member units.

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
