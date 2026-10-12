---
id: CAP-CON-002
status: backlog
started: null
completed: null
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

- [ ] Carry the effective rule's penalty destination through penalty assessment.
- [ ] Identify the exact public datetime input that is naive or otherwise invalid.
- [ ] Explain how to supply an aware datetime without silently defaulting to UTC.
- [ ] Preserve explicit occurrence times for mutating operations.

## Implementation Tasks

Task decomposition is intentionally deferred; no policy beyond the existing
timezone-awareness boundary is selected here.

## Verification

- Unit tests: each supported destination and invalid/aware datetime inputs.
- Integration tests: penalty assessment through the public contribution API.
- Manual review: no implicit timezone or penalty-destination fallback.
