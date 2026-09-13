---
id: CAP-LOCATION-001
status: shipped
started: 2026-09-13
completed: 2026-09-13
adr_refs: []
depends_on:
  - CAP-GROUP-001
blocks: []
requirements:
  - FR-LOC-001
  - FR-LOC-002
owner: domain
---

# Capability: Optional Location Metadata

## Outcome

A consumer can optionally record a group's jurisdiction and a member's
residence country using known ISO 3166-1 alpha-2 codes.

## Domain Boundary

- Inputs: optional group jurisdiction and member residence country
- Outputs: validated location metadata
- Invariants: country codes are known ISO 3166-1 alpha-2 values when supplied
- Exclusions: KYC, identity verification, tax classification, residency proof, and regulatory decisions

## Acceptance Criteria

- [x] Group jurisdiction is optional and validates known ISO 3166-1 alpha-2 codes.
- [x] Member residence country is optional and validates known ISO 3166-1 alpha-2 codes.
- [x] Missing location metadata remains valid.
- [x] No compliance, tax, or identity-verification behavior is introduced.

## Implementation Tasks

- [x] TASK-LOCATION-001: Add optional location metadata and tests.

## Verification

- `CountryCode` provides reusable ISO 3166-1 alpha-2 validation.
- `Group.jurisdiction` and `Member.residence_country` are optional normalized values.
- Tests cover omitted, valid, and invalid metadata.