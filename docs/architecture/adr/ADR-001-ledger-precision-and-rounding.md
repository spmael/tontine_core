---
id: ADR-001
title: Ledger precision and rounding policy
status: accepted
date: 2026-09-12
---

# ADR-001: Ledger Precision and Rounding Policy

## Context

CEMAC, UEMOA, Japan, the Eurozone, and the United States do not share one
universal banking rounding algorithm. ISO 4217 minor units describe normal
currency settlement precision, but they do not define the precision required for
interest, FX, allocation, tax, or other intermediate calculations.

This is especially important for JPY, XAF, and XOF, which normally settle in
whole currency units while legitimate calculations may retain fractional values.

## Decision

`tontine-core` separates calculation precision from posting and settlement
precision:

- All monetary values use `decimal.Decimal`.
- Intermediate calculations remain unquantized unless a governing rule requires
  an earlier boundary.
- Posting precision is determined by the business event, applicable law,
  contract, group rules, or external settlement system.
- ISO 4217 currency metadata provides the default currency quantum, not a global
  rounding mode.
- A rounding mode must be explicit for a financially meaningful posting.
- Cash rounding is a separate settlement adjustment and must not overwrite the
  accounting amount.
- Posted ledger entries preserve the posted amount and provenance; material
  rounding differences must remain attributable and auditable.
- Historical calculations must retain the policy or rule identity used at the
  time rather than depending on a mutable global default.

The V1 ledger accepts posted currency amounts and does not silently quantize
intermediate calculations. A future calculation or rounding capability may add
versioned `RoundingPolicy` and `RoundingResult` value objects.

## Consequences

Positive consequences:

- JPY, XAF, XOF, EUR, USD, and other currencies can share one ledger model.
- Currency settlement precision is not confused with calculation precision.
- Rounding decisions remain explicit and auditable.
- The core remains independent of banks, payment providers, and jurisdictions.

Tradeoffs:

- Callers must provide an explicit rounding policy when converting calculated
  values into posted amounts.
- The ledger does not decide product-specific legal rounding rules.
- A later rounding capability will be needed for interest, FX, tax, and unit
  calculations.

## Alternatives Rejected

- Quantizing every intermediate value to the ISO minor unit would destroy useful
  precision for JPY, XAF, XOF, FX rates, and proportional allocations.
- Choosing `ROUND_HALF_EVEN` or `ROUND_HALF_UP` globally would invent a rule that
  is not universally required by IFRS, SYSCOHADA, US GAAP, Japanese standards,
  or regional banking practice.
- Embedding COBAC, BCEAO, Japanese, European, or US product rules in the core
  ledger would violate the framework-independent domain boundary.
