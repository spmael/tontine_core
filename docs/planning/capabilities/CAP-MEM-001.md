---
id: CAP-MEM-001
status: backlog
started: null
completed: null
adr_refs: []
depends_on:
  - CAP-GROUP-001
  - CAP-CLASSIC-001
  - CAP-GOV-001
blocks: []
requirements:
  - FR-MEM-001
  - FR-MEM-002
owner: domain
---

# Capability: Member Shares and Responsibilities

## Outcome

A person can hold multiple distinct participation shares where contribution or
rotation rules operate per share, while governance remains person-based and
operational responsibilities remain separate from domain roles.

## Domain Boundary

- Inputs: member identities, participation shares, domain roles, and
  responsibilities
- Outputs: stable participation identities and responsibility-conflict findings
- Invariants: share-level obligations do not multiply a person's governance
  votes; responsibilities do not grant application permissions
- Exclusions: authentication, authorization, identity verification, and
  application-specific staffing workflows

## Acceptance Criteria

- [ ] Represent multiple stable participation shares for one member.
- [ ] Allow share-level contribution and rotation positions with person-level
  reporting roll-up.
- [ ] Keep governance eligibility and voting person-based.
- [ ] Model responsibilities separately from the existing role vocabulary.
- [ ] Detect configured incompatible responsibility assignments without
  implementing application authorization.

## Implementation Tasks

Task decomposition is intentionally deferred until share identity and
responsibility-conflict semantics are reviewed in
[`../../architecture/next-version-gap-architecture.md`](../../architecture/next-version-gap-architecture.md).

## Verification

- Unit tests: stable share identity, aggregate reporting, one-vote-per-person,
  and responsibility conflict findings.
- Integration tests: share-level contribution/rotation with person-level
  governance.
- Manual review: role compatibility and no application authorization leakage.
