---
id: ADR-008
status: accepted
date: 2026-10-21
---

# ADR-008: Stable Participation Shares and Responsibility Findings

## Context

One person may hold multiple participation shares where contributions and
rotation positions operate per share. Governance remains one vote per person.
The domain also needs to model responsibilities separately from membership
roles and identify incompatible assignments without implementing permissions.

## Decision

- Represent each participation share as a distinct immutable record with a
  stable share identifier, owning member identifier, inclusive effective cycle,
  and optional retirement effective cycle.
- A share is active for cycle `n` when `effective_cycle <= n` and either it has
  no retirement cycle or `n < retired_from_cycle`. Share-set changes are
  effective-cycle based; they do not mutate existing rotation versions.
- Existing contribution and rotation primitives may use stable share identifiers
  as their participant keys. Person-level reporting resolves those identifiers
  through the share registry and aggregates by owning member.
- Governance eligibility and voting continue to use member identifiers, not
  share identifiers.
- Responsibilities are independent named assignments. Configured unordered
  pairs are checked for the same member within the same scope, and returned as
  findings. The core does not reject assignments or enforce application access.

## Alternatives Considered

- **Participation slots owned by a mutable membership aggregate**: rejected
  because stable records are easier to reference in historical contributions
  and rotations.
- **Rewrite existing rotations when a share changes**: rejected because it
  would alter already-recorded cycle outcomes.
- **Hard-code responsibility types or enforce assignments**: rejected because
  responsibility vocabularies and operational permissions belong to the
  consuming organization or application.

## Consequences

### Positive

- Share identity and effective-cycle history are explicit and addressable.
- Existing person-based governance remains compatible.
- Responsibility conflicts can be evaluated without introducing
  authentication or authorization behavior.

### Negative or Trade-offs

- Adapters must persist share records and responsibility assignments alongside
  their owning member and scope.
- Callers must resolve share identifiers for person-level reporting.
- Conflict rules require explicit configuration; no default responsibility
  taxonomy is imposed.

## Verification

- Tests validate stable unique share IDs, ownership, effective-cycle and
  retirement boundaries, deterministic listing, and person-level roll-up.
- Tests confirm that share changes do not mutate existing rotation versions and
  governance continues to operate on member identifiers.
- Tests cover configurable same-scope responsibility findings and confirm that
  findings do not reject assignments.
