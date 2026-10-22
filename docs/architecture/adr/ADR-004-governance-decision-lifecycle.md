---
id: ADR-004
status: accepted
date: 2026-10-18
---

# ADR-004: Governance Decision Lifecycle and State Snapshots

## Context

Governance proposals currently use a mutable in-memory registry, evaluate a
yes-vote threshold against the current member set, and may infer mutation times
from the local wall clock. Proposal electorate, quorum, closing, current-cycle
eligibility, typed non-rotation effects, and rehydration behavior need explicit
rules before the reusable decision capability can be implemented.

## Decision

- Expose a versioned immutable governance snapshot (`schema_version = 1`) for
  deterministic adapter persistence and rehydration. Snapshot state includes the
  current electorate, rotation versions and exceptions, proposal lifecycle and
  votes, rulesets, and append-only audit events. Audit events are provenance, not
  the canonical replay source. The core provides no database or serializer.
- Freeze the eligible member identifiers on each proposal at creation. Later
  membership changes affect only subsequently created proposals.
- Keep approval threshold calculation as yes votes divided by the proposal's
  frozen eligible electorate, preserving the existing threshold behavior.
  Require a quorum of two-thirds of eligible members, rounded up to a whole
  voter. Yes, no, and abstain votes count toward quorum; abstentions never count
  as yes votes. Proposal policy may represent legacy threshold-only behavior
  with a zero quorum.
- Accept early evaluation only after every eligible member has voted; otherwise
  evaluation waits until the deadline. A vote at the deadline is valid, and a
  vote after it is rejected.
- Require explicit current-cycle context. Cycle-effective rule and rotation
  changes must apply strictly after the current cycle. Member exits, penalty
  waivers, and payout deferrals are decisions for the current cycle; exit
  decisions also retain the cycle in which the request was made.
- Require callers to supply timezone-aware occurrence times for governance
  mutations; do not use a hidden local-clock fallback.
- Use typed proposal effects for rotation order changes, one-cycle recipient
  overrides, activation of immutable `Ruleset` values, member exits, penalty
  waivers, and reasoned payout deferrals. The member named in an expulsion or
  their own penalty waiver is excluded from that proposal's frozen electorate.
  A one-cycle recipient override does not alter the base rotation, payout
  calculation, or unpaid-contribution eligibility.

## Alternatives Considered

- **Canonical event replay as the sole state source**: rejected because the
  current requirement calls for an explicit versioned state contract, and replay
  would make recovery depend on a full mutation sequence.
- **Both snapshots and event replay**: rejected because the package has no
  persistence adapter or event-schema migration contract; keeping two
  authoritative recovery paths would add unnecessary consistency rules.
- **Resolve proposal eligibility against current membership**: rejected because
  unrelated membership changes would rewrite an in-flight electorate.
- **Count abstentions as no votes**: rejected because the selected rule treats
  abstention as participation only.
- **Allow arbitrary proposal payloads**: rejected in favor of explicit,
  domain-specific effect types.

## Consequences

### Positive

- Proposal evaluation and historical eligibility are deterministic and
  reproducible.
- Quorum, abstention, closing, timing, and effective-cycle rules are explicit.
- Governance state can be persisted by an adapter and restored without replaying
  public mutation calls.
- Non-rotation decisions have a defined first effect type without executing
  arbitrary payloads.

### Negative or Trade-offs

- The two-thirds quorum is stricter than the previous threshold-only behavior;
  threshold-only behavior remains available only when explicitly configured
  with zero quorum.
- Adapters must version their encoding of the snapshot and handle unsupported
  schema versions explicitly.
- Proposal creation now requires current-cycle context, and lifecycle mutations
  require explicit occurrence timestamps.

## Verification

- Tests cover exact two-thirds quorum boundaries, abstentions, deadline and
  early-evaluation rules, frozen electorates, strictly future effective cycles,
  typed effects, and snapshot round trips.
- Traceability links this decision to `CAP-GOV-002` and its tasks.
