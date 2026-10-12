---
kind: requirements_register
source: BRD.md; docs/TONTINE_CORE_GAPS_v1.md (proposed future requirements)
status: active
---

# tontine-core Requirements Register

This register translates the BRD into stable, testable requirement IDs. The BRD
remains authoritative for the current implementation baseline. The
`Next-Version Gap Requirements` section records proposed future scope from
`docs/TONTINE_CORE_GAPS_v1.md`; those additions do not change the current BRD
baseline or imply that their design decisions have been made.

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

The package must create a tontine with a non-empty identifier, non-blank name,
and valid ISO 4217 base currency. Group identifiers must reject whitespace.

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
the field is metadata only and does not perform compliance or regulatory checks.

### FR-LOC-002 - Support optional member residence metadata

The package may record an optional ISO 3166-1 alpha-2 residence country for a
member; the field is metadata only and does not perform identity verification,
tax classification, or regulatory checks.

## Contribution Engine

### FR-CON-001 - Define contribution rules

The package must define amount, currency, frequency, due-date convention, grace
period, optional late penalty, and effective date. Daily, weekly, and monthly
contributions are the initial supported frequencies.

### FR-CON-002 - Create contribution cycles

The package must create cycles with start date, due date, status, expected
contributions, recorded contributions, and outstanding contributions. Payout or
allocation association is outside the current implementation baseline.

### FR-CON-003 - Record contributions

The package must record member, cycle, expected amount, actual amount, payment
date, status, external reference, and notes without processing payment.

### FR-CON-004 - Detect contribution status

The package must identify pending, paid, partial, late, and missed contributions
and report outstanding contributions.

### FR-CON-005 - Prevent duplicate contribution records

The package must reject duplicate contribution records unless an explicit
adjustment or correction path is used.

### FR-CON-006 - Assess contribution penalties

The package must assess a configured fixed penalty after the contribution due
date and grace period for late or missed contributions. Penalties must remain
separate from contribution amounts and investment units, default to the common
reserve destination, and remain unpaid until settled by an external or future
ledger operation.

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

The package must calculate net asset value, unit price, member economic value,
and member ownership percentage. Liability registries must aggregate recorded
liabilities by currency. Asset aggregation from investment records is outside
the current baseline; valuation assets remain caller-supplied.

### FR-INV-004 - Track member units

The package must use a deterministic unit-based ownership model with sufficient
precision for issuance and redemption. Unit distributions are outside the
current implementation baseline.

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

The package must provide immutable versioned rulesets with positive versions and
effective cycles and resolve the applicable ruleset for a cycle. Attaching
ruleset identifiers to historical events is outside the current baseline.

### FR-GOV-002 - Manage proposals

The package must create and open proposals, record votes, and evaluate proposals
as approved or rejected with proposer, deadline, threshold, and status data.
Expire and cancel transitions are outside the current baseline.

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

## Next-Version Gap Requirements

The following requirements formalize verified integration gaps and design-time
needs reported in `docs/TONTINE_CORE_GAPS_v1.md`. They are proposed backlog scope:
implementation tasks and unresolved product/domain decisions are intentionally
deferred.

### Stateful Domain and Ledger Queries

#### FR-API-004 - Define a state interchange contract

Stateful domain registries must provide a documented, deterministic persistence
and rehydration contract, using either a versioned state representation or a
canonical event-replay contract. Rehydration must not depend on undocumented
sequences of public mutations.

#### FR-LDG-005 - Query point-in-time balances

Ledger balance queries must support an optional timezone-aware `as_of` instant
and derive the result only from journals recorded on or before that instant.

#### FR-LDG-006 - Reuse derived ledger state for balance queries

Ledger consumers must be able to query balances without replaying the complete
journal history in application code for every request. Any index, checkpoint, or
cached state must remain derivable from the immutable journal source of truth.

### Governance and Rotation

#### FR-GOV-005 - Support proposals for non-rotation decisions

The governance capability must support a proposal and voting lifecycle that can
represent decisions beyond rotation-order changes while keeping approval effects
explicit and domain-specific.

#### FR-GOV-006 - Return approval rules and evaluation tallies

Proposal evaluation must expose an auditable tally of eligible, yes, no, abstain,
and non-voting members, and support explicit approval rules for threshold,
quorum, and participation. The existing threshold behavior must remain
representable.

#### FR-GOV-007 - Enforce proposal deadlines with explicit event times

Voting and evaluation must use explicit timezone-aware event times and enforce
the proposal's declared deadline and closing policy. A vote after the deadline
must not be accepted.

#### FR-GOV-008 - Preserve proposal eligibility context

A proposal's electorate and eligibility context must remain stable and
reproducible after membership changes, so unrelated later membership changes do
not silently invalidate an in-flight proposal.

#### FR-GOV-009 - Validate proposal effective cycles

Governance must reject a proposal whose effective cycle is not eligible under
the group's current-cycle context, and expose which cycle/date validation failed
through a specific, actionable domain error.

#### FR-GOV-010 - Propose a one-cycle rotation exception

Governance must support proposing a scoped rotation change for a single cycle
without requiring a replacement order for every active member. The base rotation
must remain available outside the approved exception's scope.

#### FR-GOV-011 - Preserve caller-supplied audit times

Mutating governance operations must accept or otherwise use an explicit
timezone-aware occurrence time so audit history records when an action happened,
not when it was later replayed.

#### FR-CLS-005 - Resolve versioned rotations independently

The classic capability must resolve the applicable immutable rotation order for
a cycle from effective-cycle rotation versions without requiring reconstruction
of governance proposal and voting history.

### Contributions and Public API Behavior

#### FR-CON-007 - Apply the configured penalty destination

Contribution penalty assessment must carry the destination configured by the
applicable contribution rule rather than silently defaulting to a different
destination.

#### NFR-API-001 - Expose consistent actionable domain errors

Public domain operations must distinguish missing records from invalid input
with documented domain errors. Repository and journal lookups must not leak
inconsistent bare built-in exceptions for expected domain failures.

#### NFR-API-002 - Make timezone requirements explicit

Public datetime inputs must retain timezone-awareness validation without
silently assuming a timezone. Errors must identify the offending input and
explain how to provide an aware datetime; mutating operations must allow the
actual occurrence time to be supplied explicitly.

### Investment Activity and Valuation

#### FR-INV-006 - Represent valuation before unit issuance

Investment valuation must represent the valid no-units-outstanding state
explicitly without requiring callers to catch an exception for that state.

#### FR-INV-007 - Read recorded investment activity

The investment activity boundary must provide deterministic read access to
recorded activity, including filtering by asset, activity type, and date range
where those fields are available.

#### FR-INV-008 - Validate investment activity against its asset

Investment activity must validate its amount and currency against the associated
asset and activity type. Cross-currency activity must be rejected or use an
explicit, auditable conversion input; zero amounts must only be accepted where
the activity type defines them as meaningful.

#### FR-INV-009 - Link activity to its authorizing decision

Investment purchases and sales must be able to retain a structured reference to
the decision authorizing the activity, separate from free-text source
provenance.

### Membership and Participation

#### FR-MEM-001 - Represent multiple participation shares per member

The domain must allow one person to hold multiple distinct participation shares
or slots where contribution and rotation rules operate per share, while
person-level governance voting remains one vote per member.

#### FR-MEM-002 - Separate member responsibilities from roles

The domain must represent work responsibilities independently of membership
roles and provide a check for conflicting assignments such as reviewing one's
own treasurer activity. These responsibilities must not implement application
authentication or authorization.

### Hybrid Rotation and Investment Tontines

#### FR-HYB-001 - Version contribution split rules

Hybrid tontines must be able to define and resolve an effective-cycle rule that
splits a recorded contribution between rotation and investment purposes.

#### FR-HYB-002 - Derive unit issuance from a recorded contribution

Hybrid investment-unit issuance must derive its amount and provenance from a
recorded contribution and an applicable split rule and valuation, and must
prevent duplicate issuance for the same contribution.

#### FR-HYB-003 - Define late and missed contribution treatment

Hybrid rules must explicitly define whether and how late or missed contributions
affect investment allocation and unit issuance.

#### FR-HYB-004 - Report a member's combined settlement position

The domain must report a member's outstanding dues, unpaid rotation entitlement,
and investment-unit position together and define how unit holdings are handled
when membership or participation ends.

#### FR-HYB-005 - Derive combined reporting from shared events

Hybrid member reporting must derive rotation cash and investment value from
shared contribution and investment-event provenance rather than unrelated
caller-supplied totals.

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

### NFR-PERF-001 - Keep repeated ledger reads independent of full-history replay

Repeated balance queries must not require consumers to replay all journals for
each read. Any performance optimization must preserve journal-derived balances
and deterministic historical results.

## Traceability Summary

| BRD area | Requirement IDs | Initial capability |
| --- | --- | --- |
| Package Foundation | FR-PKG-001, NFR-PKG-001 | CAP-PACKAGE-001 |
| Financial Account Registry | FR-ACC-001..002, NFR-ACC-001 | CAP-ACCOUNT-001 |
| Group and Membership | FR-GRP-001..004 | CAP-GROUP-001 |
| Contribution Engine | FR-CON-001..006 | CAP-CON-001 |
| Classic Tontine | FR-CLS-001..004 | CAP-CLASSIC-001 |
| Investment Tontine | FR-INV-001..005 | CAP-INVEST-001 |
| Ledger and Accounting | FR-LDG-001..004 | CAP-LEDGER-001 |
| Governance and Audit | FR-GOV-001..004 | CAP-GOV-001 |
| Statements and Reporting | FR-RPT-001..003 | CAP-REPORT-001 |
| Persistence and Public API | FR-API-001..003 | CAP-API-001 |
| Non-functional | NFR-CAL-001..NFR-SCP-001 | Cross-cutting |
| Next-version state and ledger queries | FR-API-004, FR-LDG-005..006, NFR-PERF-001 | CAP-STATE-001, CAP-LEDGER-002 |
| Next-version governance and rotation | FR-GOV-005..011, FR-CLS-005 | CAP-GOV-002, CAP-CLASSIC-002 |
| Next-version contributions and API errors | FR-CON-007, NFR-API-001..002 | CAP-CON-002, CAP-API-002 |
| Next-version investment activity | FR-INV-006..009 | CAP-INV-002 |
| Next-version membership participation | FR-MEM-001..002 | CAP-MEM-001 |
| Next-version hybrid operation | FR-HYB-001..005 | CAP-HYB-001 |
