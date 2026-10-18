---
id: CAP-INV-002
status: shipped
started: 2026-10-18
completed: 2026-10-19
adr_refs:
  - ADR-005
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

- [x] Represent the valid zero-units-outstanding valuation state explicitly.
- [x] Query recorded activities by asset, type, and available date bounds.
- [x] Validate amount and currency against both asset and activity type.
- [x] Require explicit provenance-bearing conversion inputs for any permitted
  cross-currency activity.
- [x] Retain a structured reference to the decision authorizing purchases and
  sales.
- [x] Keep activity aggregation and valuation behavior deterministic.

## Implementation Tasks

Policies are decided in
[ADR-005](../../architecture/adr/ADR-005-investment-activity-and-valuation-policy.md).

- [TASK-INV-007](../tasks/TASK-INV-007.md) - shipped: no-units valuation and
  module split
- [TASK-INV-008](../tasks/TASK-INV-008.md) - shipped: currency validation, FX
  conversion, and queries
- [TASK-GOV-006](../tasks/TASK-GOV-006.md) - shipped: typed investment
  authorization effect
- [TASK-INV-009](../tasks/TASK-INV-009.md) - shipped: decision references with
  cumulative limits
- [TASK-INV-010](../tasks/TASK-INV-010.md) - shipped: positive and
  minimum-unit activity amounts, and positive purchase and sale units

## Verification

- Unit tests: zero-units state, activity filtering, amount/type validation,
  purchase and sale units, currency mismatch, explicit conversion provenance,
  and authorization links.
- Integration tests: approved-decision reference validation through the public
  investment API.
- Manual review: no implicit FX conversion or investment execution.
