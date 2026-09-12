# Business Requirements Document (BRD)

## Project Name

**Working package name:** `tontine-core`

**Recommended repository name:** `tontine-core`

**Python import name:** `tontine`

---

## 1. Document Purpose

This document defines the business requirements for Version 1 of `tontine-core`, an open-source Python package for creating, managing, and tracking community tontines.

Version 1 focuses on two initial tontine modes:

1. **Classic Tontine** — members contribute periodically and the pooled contribution is distributed to one member according to an agreed rotation.
2. **Investment Tontine** — members contribute periodically and the group tracks how contributions are allocated to cash reserves and investment positions.

The package is designed first for small trusted groups, including diaspora communities, while remaining generic enough to support other rotating savings and community investment models in the future.

---

## 2. Background

Tontines are widely used across African communities as informal systems for saving, mutual support, access to liquidity, and collective discipline.

Many diaspora groups continue to use similar arrangements, but management is often based on:

- WhatsApp messages;
- spreadsheets;
- verbal agreements;
- bank-transfer screenshots;
- manual contribution tracking;
- trust in one or two organizers.

This creates several recurring problems:

- unclear contribution history;
- disputes about who paid and when;
- difficulty tracking missed payments;
- lack of transparent group rules;
- limited historical records;
- difficulty monitoring group assets;
- weak governance when rules change;
- no standardized way to track investment-oriented tontines.

`tontine-core` aims to provide a reusable open-source software engine for these workflows.

---

## 3. Product Vision

> Build a simple, transparent, auditable, and reusable Python engine for community tontines.

The package should allow developers to create tontine applications without rebuilding contribution logic, rotation rules, accounting, governance, and investment tracking from scratch.

The long-term ambition is to support broader community savings models such as ROSCAs, ASCAs, Njangi, Susu, Esusu, savings circles, and investment clubs while preserving the specific rules and identity of each model.

Version 1 does not attempt to solve all of these cases.

---

## 4. Product Principles

Version 1 should follow these principles:

### 4.1 Simplicity

The package should be understandable by a Python developer without requiring specialist financial-engineering knowledge.

### 4.2 Transparency

Every financially meaningful event should be traceable.

### 4.3 Rules Before Automation

The group agreement should define how the tontine operates. The software should enforce or report against those rules.

### 4.4 Ledger as Source of Truth

Financial balances should be derived from recorded transactions rather than manually maintained balance fields.

### 4.5 No Custody in Version 1

The package records financial activity but does not hold, receive, transfer, remit, or invest real client funds.

### 4.6 Framework Independence

The core package should not depend on Django, Flask, FastAPI, or another web framework.

### 4.7 Extensibility

Classic and investment tontines should be implemented as configurable strategies or rule sets rather than hard-coded tontine modes.

---

## 5. Version 1 Objective

Version 1 must allow a small group to manage an entire tontine cycle from creation to reporting.

At the end of Version 1, a developer must be able to:

1. create a tontine;
2. add members;
3. define contribution rules;
4. select a tontine mode;
5. define payout or allocation rules;
6. create contribution cycles;
7. record contributions;
8. identify outstanding contributions;
9. record classic payouts;
10. record investment allocations and positions;
11. calculate member economic ownership;
12. calculate group net asset value;
13. maintain an auditable ledger;
14. define and version governance rules;
15. create and vote on proposals;
16. generate member and group statements.

---

# 6. Scope

## 6.1 In Scope

Version 1 includes:

- tontine creation;
- member management;
- membership status;
- contribution rules;
- recurring contribution cycles;
- contribution recording;
- missed and late contribution tracking;
- classic rotation schedules;
- payout recording;
- cash reserve allocations;
- manually recorded investment positions;
- investment valuation;
- member ownership tracking;
- net asset value calculation;
- accounting ledger;
- transaction history;
- group rules;
- rule versioning;
- proposals;
- voting;
- audit events;
- member statements;
- group statements;
- basic serialization and persistence interfaces.

---

## 6.2 Out of Scope

Version 1 must not include:

- bank account connectivity;
- Wise integration;
- Revolut integration;
- Mobile Money integration;
- payment initiation;
- payment custody;
- broker APIs;
- securities execution;
- automatic bond purchase;
- automatic FX conversion;
- lending;
- credit scoring;
- insurance products;
- tokenization;
- blockchain;
- cryptocurrency;
- public fundraising;
- external investor onboarding;
- KYC or AML workflows;
- tax calculation;
- regulatory reporting;
- portfolio optimization;
- market-data feeds;
- automated pricing feeds.

These features may be considered separately in later versions.

---

# 7. Target Users

## 7.1 Primary User

A developer integrating a tontine, savings-circle, or community-finance package.

## 7.2 Secondary Users

Applications built with the package may serve:

- tontine organizers;
- tontine members;
- diaspora savings groups;
- investment clubs;
- community associations;
- mutual-support groups.

Version 1 itself is a Python library and does not provide the final end-user interface.

---

# 8. Core Domain Model

The package should treat a tontine as the combination of:

> **Members + Contribution Rules + Allocation Rules + Distribution Rules + Governance Rules + Ledger**

The software should avoid embedding all business behavior directly inside one large `Tontine` class.

---

## 8.1 Tontine

Represents one community financial group.

Minimum attributes:

- unique identifier;
- name;
- description;
- base currency;
- creation date;
- status;
- current ruleset;
- contribution frequency;
- contribution amount;
- active cycle.

Suggested statuses:

- `draft`;
- `active`;
- `paused`;
- `completed`;
- `closed`.

---

## 8.2 Member

Represents one participant.

Minimum attributes:

- unique identifier;
- display name;
- membership start date;
- membership status;
- role.

Suggested roles:

- `member`;
- `treasurer`;
- `administrator`.

Suggested statuses:

- `invited`;
- `active`;
- `suspended`;
- `left`;
- `removed`.

Personal identity verification is outside Version 1.

---

## 8.3 Contribution Rule

Defines the normal member contribution.

Minimum requirements:

- contribution amount;
- currency;
- frequency;
- due-date convention;
- grace period;
- optional late penalty;
- effective date.

Version 1 should initially support:

- monthly contributions.

The internal design should allow additional frequencies later.

---

## 8.4 Cycle

Represents one contribution and distribution period.

Example:

`January 2027`

A cycle should track:

- start date;
- contribution due date;
- cycle status;
- expected contributions;
- recorded contributions;
- outstanding contributions;
- associated payout or allocation.

Suggested statuses:

- `scheduled`;
- `open`;
- `due`;
- `closed`.

---

## 8.5 Contribution

Represents a member contribution recorded by the group.

Minimum attributes:

- member;
- cycle;
- expected amount;
- actual amount;
- payment date;
- status;
- external reference;
- notes.

Suggested statuses:

- `pending`;
- `paid`;
- `partial`;
- `late`;
- `missed`.

The package records that payment occurred.

It does not process the payment.

---

# 9. Tontine Modes

Version 1 must support two presets built on common underlying rules.

---

## 9.1 Classic Tontine

In the Classic Tontine mode:

- each member contributes an agreed amount;
- one designated member receives the cycle distribution;
- recipients rotate according to an agreed sequence.

Example:

```text
Members: 5
Contribution: JPY 30,000 per member
Monthly pool: JPY 150,000

January: Member A
February: Member B
March: Member C
April: Member D
May: Member E
```

### Business Requirements

The package must:

- define the recipient order;
- validate that each active member has a valid rotation position;
- identify the recipient for each cycle;
- calculate the expected payout;
- record the payout;
- retain historical recipient data;
- prevent accidental duplicate payouts for the same cycle;
- report unpaid contributions before closing a cycle.

The package should allow the group to decide whether a payout may occur despite unpaid contributions.

This must be a configurable governance rule, not a hard-coded assumption.

---

## 9.2 Investment Tontine

In Investment Tontine mode:

- member contributions remain economically attributable to members;
- contributions may be allocated across one or more group asset categories;
- investment transactions and positions are manually recorded;
- the package calculates group asset value and member ownership.

Example allocation:

```text
Cash reserve                  10%
Short-term liquid assets      20%
Diversified investments       40%
African sovereign bonds       30%
```

These percentages are examples only and must not be hard-coded.

### Business Requirements

The package must support:

- configurable allocation rules;
- cash balances;
- investment asset definitions;
- purchase records;
- sale records;
- income records;
- fees;
- manual valuation updates;
- total asset calculation;
- total liability calculation;
- net asset value calculation;
- member ownership calculation;
- member investment statements.

Version 1 must not connect to a broker or execute investments.

---

# 10. Member Economic Ownership

Investment-mode tontines must not assume that all members permanently own equal percentages.

Ownership may change because of:

- missed contributions;
- late joining;
- additional contributions;
- member exit;
- distributions;
- reinvestment.

Version 1 should use an internal unit-based ownership model.

Conceptually:

```text
NAV = Assets - Liabilities

Unit Price = NAV / Total Units Outstanding
```

New eligible contributions may create units according to the applicable unit price.

Exact unit issuance rules must be deterministic and testable.

The package must support sufficient decimal precision for financial calculations.

Floating-point arithmetic must not be used for monetary values.

---

# 11. Ledger and Accounting

## 11.1 Requirement

The ledger must be the financial source of truth.

Balances should be calculated from ledger entries rather than manually updated totals.

## 11.2 Accounting Model

Version 1 should implement double-entry accounting.

Every financial event must create balanced entries.

Example contribution:

```text
Debit   Cash / Receivable
Credit  Member Contribution Capital
```

Example investment purchase:

```text
Debit   Investment Asset
Credit  Cash
```

Example investment income:

```text
Debit   Cash
Credit  Investment Income
```

The exact chart of accounts should be configurable enough for future expansion while remaining simple in Version 1.

## 11.3 Ledger Requirements

Each journal entry must include:

- unique identifier;
- timestamp;
- transaction date;
- description;
- debit entries;
- credit entries;
- source event;
- optional reference;
- creator or actor identifier where available.

Posted ledger entries should be immutable.

Corrections should be made using reversal or adjustment entries.

---

# 12. Investment Asset Tracking

Version 1 should support manual asset records.

Example asset types:

- cash;
- deposit;
- bond;
- equity;
- fund;
- other.

Minimum asset fields:

- unique identifier;
- name;
- symbol or reference;
- asset type;
- currency;
- quantity;
- acquisition cost;
- current unit value;
- valuation date.

The package should support assets denominated in currencies different from the tontine base currency.

However, automated FX conversion is outside Version 1.

If a valuation requires an FX rate, that rate must be supplied manually by the consuming application.

---

# 13. Governance

A tontine is not only an accounting structure.

Version 1 must also model basic group governance.

---

## 13.1 Ruleset

Each tontine must have a ruleset.

Examples of rules:

- contribution amount;
- due date;
- grace period;
- late contribution policy;
- payout order;
- payout eligibility;
- emergency withdrawal policy;
- new-member admission;
- member exit;
- voting threshold;
- ruleset amendment threshold.

---

## 13.2 Rule Versioning

Rules must not simply be overwritten.

When approved changes occur:

```text
Ruleset v1
Effective: 1 January 2027

Ruleset v2
Effective: 1 June 2027
```

Historical events must continue to reference the rules applicable at the time.

---

## 13.3 Proposal

Members with appropriate permissions should be able to create proposals.

Minimum fields:

- proposal ID;
- title;
- description;
- proposer;
- creation date;
- voting deadline;
- required approval threshold;
- status.

Suggested statuses:

- `draft`;
- `open`;
- `approved`;
- `rejected`;
- `expired`;
- `cancelled`.

---

## 13.4 Voting

Version 1 should support:

- one-member-one-vote;
- yes;
- no;
- abstain.

Weighted voting is outside Version 1.

The system must calculate whether the required approval threshold has been reached.

---

# 14. Auditability

The package must record significant non-financial events.

Examples:

- tontine created;
- member added;
- member removed;
- rules changed;
- contribution recorded;
- contribution corrected;
- payout recorded;
- investment transaction recorded;
- valuation updated;
- proposal created;
- vote submitted;
- cycle closed.

Audit records should be append-only.

---

# 15. Statements and Reporting

Version 1 should expose structured report objects or services.

Rendering PDF, Excel, or web pages is outside the core package.

---

## 15.1 Member Statement

A member statement should include:

- member information;
- contribution history;
- outstanding contributions;
- penalties if applicable;
- payouts received;
- current investment units;
- estimated economic ownership;
- current attributable value.

---

## 15.2 Group Statement

A group statement should include:

- active members;
- current cycle;
- expected contributions;
- received contributions;
- outstanding contributions;
- cash balance;
- investment value;
- liabilities;
- NAV;
- historical payouts;
- pending proposals.

---

# 16. Permissions

Version 1 should provide basic domain-level authorization concepts.

Suggested roles:

### Member

Can:

- view group information;
- view own statement;
- submit votes.

### Treasurer

Can additionally:

- record contributions;
- record payouts;
- record investment transactions;
- record valuations.

### Administrator

Can additionally:

- manage members;
- create ruleset proposals;
- manage group configuration.

Application-level authentication remains outside the package.

---

# 17. Currency and Numerical Requirements

Financial values must use:

```python
decimal.Decimal
```

and never binary floating-point numbers.

Every tontine must define one base currency.

Version 1 should support ISO 4217 currency codes such as:

- `JPY`;
- `XAF`;
- `EUR`;
- `USD`.

Multi-currency assets may be recorded.

FX rates must be externally supplied.

---

# 18. Time and Date Requirements

All domain dates must use standard Python date or timezone-aware datetime objects where appropriate.

The package must not assume a specific country timezone.

Contribution due dates should be represented according to the tontine rules.

---

# 19. Persistence

`tontine-core` should remain framework-independent.

The business domain must not require Django ORM models.

Version 1 should expose entities and repository interfaces that allow consuming applications to use:

- in-memory persistence;
- SQL databases;
- Django ORM adapters;
- SQLAlchemy adapters;
- other persistence technologies.

A simple in-memory implementation should be provided for testing and examples.

---

# 20. Public API Design Goals

The library should aim for a readable API.

Illustrative only:

```python
from decimal import Decimal

from tontine import Tontine
from tontine.strategies import ClassicRotation

group = Tontine.create(
    name="Tokyo Cameroon Circle",
    currency="JPY",
    contribution_amount=Decimal("30000"),
    strategy=ClassicRotation(),
)
```

Example contribution:

```python
group.record_contribution(
    member_id="member-001",
    amount=Decimal("30000"),
    cycle="2027-01",
)
```

Exact API design belongs to the technical design stage rather than this BRD.

---

# 21. Validation and Business Rules

Version 1 must prevent or flag:

- duplicate member identifiers;
- negative contributions;
- zero or negative normal contribution amounts;
- duplicate contribution records without explicit adjustment handling;
- duplicate classic payouts;
- payouts to invalid members;
- investment sale quantities greater than available quantity;
- unbalanced ledger transactions;
- invalid voting thresholds;
- votes from ineligible members;
- modifications to posted ledger entries;
- rule changes without a new ruleset version.

Business errors should use clear domain-specific exception classes.

---

# 22. Non-Functional Requirements

## 22.1 Reliability

Financial calculations must be deterministic.

## 22.2 Testability

Core business rules must be unit-testable without a database or web framework.

## 22.3 Documentation

Every public class and function must have concise docstrings.

The repository should include practical examples for both tontine modes.

## 22.4 Code Quality

The project should follow:

- modern Python packaging standards;
- PEP 8;
- type hints;
- clear naming;
- small modules;
- explicit domain rules.

## 22.5 Python Version

Initial target:

```text
Python >= 3.12
```

Avoid unnecessarily restricting the package to a very recent Python version unless a required feature justifies it.

## 22.6 Security

The package must:

- avoid storing secrets;
- avoid embedding bank credentials;
- avoid logging sensitive financial data unnecessarily;
- expose clear interfaces for consuming applications to implement access control.

---

# 23. Regulatory Boundary

`tontine-core` is software infrastructure.

Version 1 must not present itself as:

- a bank;
- an investment manager;
- a broker;
- a remittance provider;
- an insurer;
- a custodian;
- a regulated investment fund.

The package may calculate, record, simulate, and report investment-related activity.

Actual financial transactions must occur through external institutions chosen by the users of applications built on top of the package.

The project documentation should clearly state that developers and users are responsible for determining legal and regulatory obligations in their jurisdictions.

---

# 24. Recommended Package Architecture

A preliminary package structure could be:

```text
tontine-core/
├── src/
│   └── tontine/
│       ├── groups/
│       ├── members/
│       ├── cycles/
│       ├── contributions/
│       ├── payouts/
│       ├── investments/
│       ├── ledger/
│       ├── governance/
│       ├── reports/
│       ├── strategies/
│       ├── repositories/
│       └── exceptions.py
│
├── tests/
├── examples/
├── docs/
├── README.md
├── BRD.md
├── LICENSE
└── pyproject.toml
```

This is a starting point, not a mandatory final architecture.

Avoid creating modules merely to satisfy a folder structure.

---

# 25. Version 1 Epics

## Epic 1 — Group and Membership

Deliver:

- tontine creation;
- member creation;
- membership management;
- roles.

## Epic 2 — Contribution Engine

Deliver:

- contribution rules;
- monthly cycles;
- expected contributions;
- contribution recording;
- late and missing contribution detection.

## Epic 3 — Classic Tontine

Deliver:

- payout rotation;
- recipient determination;
- payout calculation;
- payout recording.

## Epic 4 — Financial Ledger

Deliver:

- chart of accounts;
- journal entries;
- double-entry validation;
- immutable posting;
- adjustments and reversals.

## Epic 5 — Investment Tontine

Deliver:

- allocation rules;
- investment positions;
- purchases;
- sales;
- income;
- manual valuations;
- NAV calculation;
- member units.

## Epic 6 — Governance

Deliver:

- rulesets;
- versioning;
- proposals;
- voting.

## Epic 7 — Reporting

Deliver:

- member statement;
- group statement;
- contribution status report;
- investment summary.

## Epic 8 — Developer Experience

Deliver:

- package installation;
- typed public API;
- examples;
- documentation;
- test suite.

---

# 26. Version 1 Acceptance Criteria

Version 1 is complete when the following scenario can be executed entirely through the package API.

A developer can:

1. create a JPY tontine;
2. add five members;
3. define a JPY 30,000 monthly contribution;
4. create a five-month cycle schedule;
5. configure classic rotation;
6. record each member's monthly contributions;
7. identify late and missing contributions;
8. calculate the classic monthly payout;
9. record the payout;
10. create an investment-mode tontine;
11. record the same five members' contributions;
12. allocate contributions between cash and investments;
13. record investment purchases manually;
14. update investment valuations;
15. calculate group NAV;
16. calculate each member's economic ownership;
17. create a proposal;
18. record votes;
19. approve a new ruleset;
20. generate member and group statements;
21. reconstruct all financial balances from the ledger;
22. inspect an audit history for major events.

All critical financial calculations must have automated tests.

---

# 27. Version 1 Success Metrics

Because Version 1 is primarily an open-source engine, initial success should be measured through usability rather than revenue.

Suggested pilot metrics:

- one real five-member tontine successfully modeled;
- six consecutive monthly cycles recorded;
- zero unexplained balance differences;
- all group members able to reconcile their contribution history;
- all rule changes traceable;
- all investment ownership calculations reproducible;
- no manual balance overrides required;
- at least one external developer able to install and use the package from documentation.

---

# 28. Future Considerations

Possible later capabilities include:

- hybrid tontines;
- emergency-reserve modules;
- configurable allocation waterfalls;
- additional contribution frequencies;
- member loans;
- insurance contribution planning;
- external payment-provider integrations;
- bank reconciliation;
- broker integrations;
- automatic market prices;
- FX feeds;
- richer accounting;
- multi-language support;
- REST API adapters;
- Django integration package;
- tokenized ownership experiments;
- regulated investment structures.

These are not commitments for Version 1.

---

# 29. Key Product Decision

Version 1 should prove that a tontine can be represented as a reliable and transparent software domain.

The first release should therefore prioritize:

> **correct rules, correct accounting, transparent ownership, and good governance**

over payments, integrations, automation, or advanced investment features.

If the financial core cannot be trusted, additional integrations only make mistakes happen faster.

---

# 30. Recommended First Implementation

The first real-world pilot should use one small trusted group.

Recommended setup:

```text
Members:       5
Currency:      JPY
Frequency:     Monthly
Pilot length:  6 months

Pilot A:
Classic rotation tontine

Pilot B:
Investment tracking tontine
with manual asset transactions
```

Real funds should remain in external accounts.

`tontine-core` should initially act as the group's shared financial record and rules engine.
