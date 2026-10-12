---
id: CAP-API-002
status: backlog
started: null
completed: null
adr_refs: []
depends_on:
  - CAP-API-001
blocks: []
requirements:
  - NFR-API-001
  - NFR-API-002
owner: package-boundary
---

# Capability: Actionable Public API Errors and Time Semantics

## Outcome

Consumers receive consistent domain errors for expected invalid and missing
record conditions and clear guidance for required timezone-aware datetime values.

## Domain Boundary

- Inputs: public API calls, identifiers, and datetime values
- Outputs: documented domain exceptions and explicit timestamp semantics
- Invariants: expected domain failures do not leak inconsistent built-in lookup
  exceptions; naive datetimes are never silently assigned a timezone
- Exclusions: application form validation, authentication, implicit UTC
  conversion, and framework-specific exception types

## Acceptance Criteria

- [ ] Use documented domain errors consistently for expected missing-record and
  invalid-input failures.
- [ ] Identify the failing field or parameter in datetime validation errors.
- [ ] Explain how a caller supplies an aware datetime.
- [ ] Keep occurrence times explicit for auditable mutations.
- [ ] Preserve framework independence of public error types.

## Implementation Tasks

Task decomposition is intentionally deferred until the relevant domain
boundaries and public error compatibility are reviewed.

## Verification

- Unit tests: missing journal/record errors, invalid input errors, and naive
  versus timezone-aware datetime inputs.
- Integration tests: public API error behavior without framework adapters.
- Manual review: exception compatibility and error-message actionability.
