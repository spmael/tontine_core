---
id: CAP-INV-002
status: backlog
started: null
completed: null
adr_refs: []
depends_on:
  - CAP-INV-001
  - CAP-GOV-002
blocks: []
requirements:
  - FR-INV-006
  - FR-INV-007
  - FR-INV-008
  - FR-INV-009
owner: domain
---

# Capability: Investment Activity Queries and Validation

## Outcome

A consumer can inspect recorded investment activity, validate it against its
asset and activity type, represent a no-units valuation state, and retain a
structured authorization reference for purchases and sales.

## Domain Boundary

- Inputs: investment assets, activities, unit totals, valuations, and approved
  decision references
- Outputs: deterministic activity queries and explicit valuation/activity
  validation results
- Invariants: asset/activity currency is consistent or conversion is explicit;
  query order is deterministic; authorization provenance is structured
- Exclusions: broker access, market-data retrieval, automatic FX, and investment
  execution

## Acceptance Criteria

- [ ] Represent the valid zero-units-outstanding valuation state explicitly.
- [ ] Query recorded activities by asset, type, and available date bounds.
- [ ] Validate amount and currency against both asset and activity type.
- [ ] Require explicit provenance-bearing conversion inputs for any permitted
  cross-currency activity.
- [ ] Retain a structured reference to the decision authorizing purchases and
  sales.
- [ ] Keep activity aggregation and valuation behavior deterministic.

## Implementation Tasks

Task decomposition is intentionally deferred until the zero-unit valuation and
cross-currency policies are reviewed in
[`../../architecture/next-version-gap-architecture.md`](../../architecture/next-version-gap-architecture.md).

## Verification

- Unit tests: zero-units state, activity filtering, amount/type validation,
  currency mismatch, explicit conversion provenance, and authorization links.
- Integration tests: approved-decision reference validation through the public
  investment API.
- Manual review: no implicit FX conversion or investment execution.
