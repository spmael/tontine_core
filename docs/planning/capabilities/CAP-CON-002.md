---
id: CAP-CON-002
status: shipped
started: 2026-10-18
completed: 2026-10-18
adr_refs: []
depends_on:
  - CAP-CON-001
blocks: []
requirements:
  - FR-CON-007
  - NFR-API-002
owner: domain
---

# Capability: Contribution Penalty and Time Inputs

## Outcome

A consumer can assess a contribution penalty using the destination configured
for the applicable rule and receive clear validation guidance for invalid
datetime inputs.

## Domain Boundary

- Inputs: effective contribution rules, penalty assessments, and aware datetimes
- Outputs: penalty records with authoritative destinations and actionable
  datetime validation errors
- Invariants: penalty destination is not silently replaced; naive datetime values
  are not silently interpreted in an assumed timezone
- Exclusions: penalty settlement, ledger posting, payment processing, and
  implicit timezone conversion

## Acceptance Criteria

- [x] Carry the effective rule's penalty destination through penalty assessment.
- [x] Identify the exact public datetime input that is naive or otherwise invalid.
- [x] Explain how to supply an aware datetime without silently defaulting to UTC.
- [x] Preserve explicit occurrence times for mutating operations.

## Implementation Tasks

- `TASK-CON-004` implements configured penalty destination propagation and
  verifies aware datetime inputs and explicit occurrence timestamps.

## Verification

- Unit tests: all five destinations, named naive timestamp inputs, and explicit
  occurrence times in `tests/contributions/`.
- Public API tests: `tests/test_public_api.py` verifies late and missed
  assessments created from a contribution rule.
- Manual review: rule settings are copied by `ContributionCycle.from_rule`;
  default reserve behavior remains only for rules/cycles without an override.
