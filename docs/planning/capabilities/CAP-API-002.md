---
id: CAP-API-002
status: partial
started: 2026-10-12
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
  conversion, framework-specific exception types, and retaining `KeyError` as
  the public missing-record error

## Acceptance Criteria

- [ ] Use documented domain errors consistently for expected missing-record and
  invalid-input failures.
- [ ] Identify the failing field or parameter in datetime validation errors.
- [ ] Explain how a caller supplies an aware datetime.
- [ ] Keep occurrence times explicit for auditable mutations.
- [ ] Preserve framework independence of public error types.

## Implementation Tasks

- [x] [TASK-API-003](../tasks/TASK-API-003.md): Standardize missing-record domain errors.
- [ ] [TASK-API-004](../tasks/TASK-API-004.md): Make timezone validation errors actionable.
- [ ] [TASK-API-005](../tasks/TASK-API-005.md): Accept explicit audit occurrence times.

## Verification

- Unit tests: missing journal/record errors, invalid input errors, and naive
  versus timezone-aware datetime inputs.
- Integration tests: public API error behavior without framework adapters.
- Manual review: exception compatibility and error-message actionability.
