---
id: ADR-005
status: accepted
date: 2026-10-18
amended: 2026-10-19
---

# ADR-005: Investment Activity Validation, Valuation, and Authorization

## Context

`CAP-INV-002` requires a no-units valuation state, activity validation against
its asset, explicit handling of cross-currency activity, and a structured link
from purchases and sales to their authorizing decision. Today
`InvestmentValuation` rejects zero units outstanding, activity accepts any
non-negative amount in any currency, and investment provenance is free text.
Governance proposals carry typed effects, but only rotation and ruleset effects
exist and proposals require a rotation order.

## Decision

### No-units valuation

- `InvestmentValuation` accepts `units_outstanding == 0` and exposes a
  `has_units_outstanding` flag. NAV remains assets less liabilities.
- `unit_price`, `member_value`, and `member_ownership_percentage` return `None`
  when no units are outstanding, because no price can be derived by dividing by
  zero. Callers branch on the value or flag, not on an exception.
- The return types of those members become optional; this is an accepted
  pre-1.0 breaking change.

### Cross-currency activity

- Each asset has one currency. An activity in that currency needs no
  conversion input.
- An activity in a different currency is accepted only with an explicit
  `FxRate` whose currency pair is exactly the activity and asset currencies.
  Either quotation direction is accepted. A rate for any other pair, or a
  cross-currency activity without a rate, is rejected.
- The activity retains its original amount and currency, the supplied rate with
  its source provenance, and the derived asset-currency amount.
- Per ADR-001 and ADR-003, the derived amount keeps full Decimal precision; no
  rounding is applied at recording time. Rate staleness remains a caller policy
  using `is_rate_current`.
- Example: a JPY 550 broker fee on a USD-denominated asset is recorded with a
  supplied USD/JPY rate and retains both the JPY 550 and the derived USD amount.

### Authorization reference and typed investment effect

- Purchases and sales may carry an optional structured decision reference that
  identifies the governance proposal. Income and fee activity reject it.
- Governance gains an `InvestmentAuthorizationEffect` with asset identifier,
  activity type (purchase or sale), maximum amount, and currency. Proposals that
  carry this effect do not require a rotation order; existing rotation proposal
  construction remains compatible.
- When a reference is supplied, validation uses a governance lookup supplied to
  the activity boundary, not a direct dependency on registry internals. The
  referenced proposal must be approved and carry an investment authorization
  effect that matches the activity's asset and type.
- The effect limit is cumulative: the total asset-currency amount of all
  activities referencing the same decision may not exceed the effect maximum.
  The effect currency must match the asset currency.

### Query defaults

- Activity queries filter by asset, activity type, and inclusive
  `effective_date` bounds.
- Results are ordered by `effective_date`, then `recorded_at`, then `event_id`.

### Zero and minimum activity amounts

Amended 2026-10-19 after review by an external auditor (IFRS 9 and SYSCOHADA),
an investment operations lead, a compliance officer, and a ledger architect.

- Purchase, sale, income, and fee amounts must be strictly positive. No current
  activity type gives zero a meaning, which satisfies `FR-INV-008`.
- One per-type table (`{activity type: allow zero}`) drives the rule; every
  entry is `False`. Allowing zero for a future type is one entry plus a test.
- `amount` is the payment or fair value, not only cash. An in-kind transfer is
  recorded at a positive fair value.
- Income and fees are recorded gross. A tax withholding or fee rebate is a
  separate record, never netted into one amount, and never a net zero.
- An amount below the smallest ISO 4217 unit of its currency is rejected, not
  rounded, so 0.4 XAF cannot become a zero record. The same check applies to
  the converted asset-currency amount. Finer precision above that unit (for
  example 1.5 XAF) is kept unquantized per ADR-001. Codes without an ISO minor
  unit, such as XAU, need only be positive.
- The rejection message names the supported path: a note for a waiver or
  cancellation, a reversal of the original for a correction, or the planned
  corporate-action type for unit-only events. This keeps users from working
  around the rule with token 1 XAF records.
- Purchases and sales require a strictly positive `units` asset quantity,
  driven by a per-type `{activity type: units required}` table. Zero, negative,
  and non-finite units are rejected with the same guidance. Fractional units
  are valid and are not checked against a currency unit. Income and fees carry
  no units and reject them. Asset `units` are distinct from member ownership
  units in the unit ledger.
- Unit-only events (split, bonus shares, consolidation, write-off) belong to a
  planned corporate-action or adjustment type and cannot be recorded until it
  exists. A full write-off is represented by the zero-units valuation state.

Follow-ups, decided in principle but not built:

- Corrections use a linked, append-only reversal entry with a reason that
  reverses the original amount. Negative activity amounts stay rejected so they
  cannot become an unlinked correction path.
- Waivers and cancellations are typed events visible in member statements, not
  only in the audit trail.

## Alternatives Considered

- **Dedicated pre-issuance valuation type**: rejected because every caller would
  need type branching for one state that a flag and optional values express.
- **Reject all cross-currency activity**: rejected because real broker fees and
  income are often charged or paid in the account currency, not the asset
  currency.
- **Quantize converted amounts to ISO minor units**: rejected because ADR-001 and
  ADR-003 preserve source precision until an explicit posting rounding policy.
- **Approval-only authorization check**: rejected because any approved proposal,
  including an unrelated rotation change, could be cited for an investment.
- **Single-use authorization**: rejected in favor of a cumulative limit so one
  decision can authorize a purchase executed in several fills.
- **Allow zero amounts, or wait for further advisor review**: rejected because
  every realistic zero-cash case is a unit-only event, a waiver, or a
  correction, none of which is a purchase, sale, income, or fee. A zero purchase
  can also make a decision look executed while hiding off-book spending.
  Starting strict is reversible; loosening later breaks no caller, while
  tightening later would leave invalid rows in append-only history.

## Consequences

### Positive

- Valuation before the first unit issue is a normal, exception-free state.
- Cross-currency activity is auditable, with original amount, rate, and source
  retained.
- Investment activity can be tied to a decision that actually authorized that
  asset, type, and amount.
- Zero, negative, and sub-unit amounts cannot make a decision look executed or
  enter the append-only history.

### Negative or Trade-offs

- Valuation members become optional, which affects existing callers.
- Governance proposals must be generalized beyond rotation-specific fields.
- Callers must supply FX rates and a governance lookup for validated
  cross-currency or authorized activity.
- Unit-only events, waivers, and corrections cannot be recorded as activity
  until the corporate-action, typed waiver, and reversal follow-ups exist.
- The minor-unit table is maintained in code, because pycountry carries no ISO
  4217 minor-unit data.

## Verification

- Tests cover zero-units valuation, same- and cross-currency activity, wrong or
  missing FX pairs, reversed rate direction, unquantized derived amounts,
  authorization matching, cumulative limits, unapproved or mismatched
  decisions, references on income or fee, and deterministic query order.
- Tests cover zero spellings (`0`, `0.00`, `-0`, `0E-10`), negative and
  non-finite amounts for every type, sub-unit XAF and EUR amounts, the smallest
  valid amount per currency, and converted amounts below the asset unit.
- Tests cover required, positive, fractional, zero, negative, and non-finite
  purchase and sale units, and units rejected on income and fees.
- Traceability links this decision to `CAP-INV-002` and its tasks.
