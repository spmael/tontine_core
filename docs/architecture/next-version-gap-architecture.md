# Next-Version Gap Architecture

## Purpose and Status

This note translates verified integration gaps in
[`../TONTINE_CORE_GAPS_v1.md`](../TONTINE_CORE_GAPS_v1.md) into architectural
boundaries for proposed next-version work. It is a design map, not an accepted
ADR: the listed directions do not resolve the open domain choices below and do
not change the current implementation baseline in `BRD.md`.

Planning ownership is recorded in
[`../planning/requirements.md`](../planning/requirements.md) and the
next-version capabilities listed in
[`../planning/capabilities/README.md`](../planning/capabilities/README.md).
Implementation task decomposition is intentionally deferred.

## Architectural Boundaries

### Stateful Registries and Ledger Projections

- Stateful registries need one documented, deterministic state interchange
  contract. A versioned snapshot and a canonical event-replay contract are both
  viable; the public shape and compatibility policy remain undecided.
- Governance and ledger state must be rehydratable without undocumented
  sequences of mutating calls or revalidation against mutable current state.
- The immutable ledger journal remains the source of truth. Running balances,
  indexes, and checkpoints are derived projections and must be rebuildable.
- Ledger projection/query APIs, rather than application code, own efficient
  current and point-in-time balance reads.
- These boundaries are tracked by FR-API-004, FR-LDG-005..006, NFR-PERF-001,
  CAP-STATE-001, and CAP-LEDGER-002.

### Governance Decisions and Rotation History

- Separate the reusable proposal/voting lifecycle from the domain effect of an
  approval. Rotation changes and other decisions may share voting mechanics but
  must preserve typed, auditable effects.
- Capture the electorate context used by an open proposal so later membership
  changes do not rewrite its original eligibility.
- Use explicit occurrence times for votes, evaluations, ruleset changes, and
  audit records. Enforce deadlines and effective-cycle rules against explicit
  current-time/current-cycle context; do not infer either from wall-clock state
  hidden inside a registry.
- Keep rotation selection a deterministic lookup over immutable, effective-cycle
  rotation versions. Governance may approve a version, but resolving the order
  for a cycle must not require replaying every proposal and vote.
- A one-cycle rotation exception must remain scoped to its approved cycle and
  leave the base rotation intact.
- These boundaries are tracked by FR-GOV-005..011, FR-CLS-005, CAP-GOV-002,
  and CAP-CLASSIC-002.

### Contributions, Investment Activity, and Valuation

- Contribution penalty assessment must carry the destination from the effective
  contribution rule; it must not silently substitute a default.
- Keep strict timezone-awareness validation. Never silently reinterpret a naive
  datetime as UTC; identify the invalid public parameter and give callers a
  clear correction path.
- Investment activity must be both recordable and queryable. Validate activity
  type, positive/non-zero policy, and asset currency consistently. Any
  cross-currency activity must use an explicit, provenance-bearing conversion
  input rather than implicit conversion.
- Represent the no-units-outstanding valuation state explicitly, while preserving
  the mathematical constraint that a unit price cannot be derived by division
  when the denominator is zero.
- Keep decision authorization as structured provenance, not free-form source
  text. Any authorization validation must use the governance decision boundary.
- These boundaries are tracked by FR-CON-007, FR-INV-006..009, NFR-API-002,
  CAP-CON-002, CAP-INV-002, and CAP-API-002.

### Membership Shares and Responsibilities

- Distinguish a person from that person's participation shares/slots. Where rules
  act per share, each share needs a stable identity; governance eligibility and
  voting remain person-based unless a future decision explicitly changes that
  rule.
- Keep organizational responsibilities separate from the closed domain role
  vocabulary and from application authentication/authorization.
- Model separation-of-duties checks as domain validation/reporting, without
  granting or enforcing application permissions.
- These boundaries are tracked by FR-MEM-001..002 and CAP-MEM-001.

### Hybrid Rotation and Investment Behavior

- Add an explicit domain boundary to connect contribution events to rotation
  allocation and investment-unit issuance; do not couple the classic and
  investment modules through hidden side effects.
- Resolve contribution split rules by effective cycle and derive issuance from
  the recorded contribution, applicable split, and valuation. Preserve the
  contribution identifier as traceable issuance provenance and enforce
  idempotency.
- Keep missed/late contribution policy and member-exit settlement explicit; do
  not infer financial outcomes from membership state alone.
- Combined reporting must project both rotation and investment positions from
  the shared event lineage. It must not become a second source of balances.
- These boundaries are tracked by FR-HYB-001..005 and CAP-HYB-001.

## Decisions to Resolve Before Task Breakdown

These choices affect public API shape or financial/governance behavior and remain
open; the capability backlog must not be treated as choosing an answer:

1. Registry state: versioned snapshots, canonical event replay, or both; required
   schema compatibility and migration behavior.
2. Proposal eligibility: store an electorate snapshot, store a version/reference
   to membership state, or explicitly invalidate proposals when membership
   changes.
3. Proposal evaluation: quorum definition, abstention treatment, full
   participation, and whether early evaluation is permitted when all members
   have voted.
4. Proposal timing: which boundary supplies the current cycle and time, and how
   to handle an already-open or already-closed effective cycle.
5. Rotation exceptions: whether the exception inserts, replaces, or otherwise
   modifies a recipient slot, and how payout amount/eligibility is derived.
6. Investment valuation with zero units: a tagged empty result versus a dedicated
   constructor/value, and which fields are meaningful in that state.
7. Cross-currency investment activity: reject mismatched currency, or accept an
   explicit conversion record with a defined accounting point.
8. Shares: whether share identity belongs to membership, a participation
   aggregate, or a separate domain entity, and how share changes affect existing
   rotations.
9. Hybrid rules: split units, whether the rule applies to expected or actually
   received contribution amounts, late/missed treatment, and exit/settlement
   behavior.
10. Separation of duties: which responsibility combinations conflict and
    whether conflicts reject updates or are returned as findings.

## Delivery Guardrails

- Treat all requirements in the next-version section as proposed backlog, not
  implemented behavior or a change to Version 1 guarantees.
- Keep persistence, database, network, payment, and web-framework adapters
  outside the domain core.
- Do not change the ledger source-of-truth rule, add implicit financial
  conversions, or select governance/settlement policies as implementation
  shortcuts.
- Record resolved architecture choices as ADRs before implementation tasks rely
  on them.
