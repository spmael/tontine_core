---
id: TASK-HYB-001
status: ready
started: null
completed: null
adr_refs:
  - ADR-006
requirements:
  - FR-HYB-001
  - FR-HYB-003
capability: CAP-HYB-001
owner: domain
---

# Task: Version hybrid allocation rules

## Goal

Define immutable, versioned hybrid rule sets resolved by effective cycle.

## Context

ADR-006: fund share in basis points, partial-payment order, catch-up policy, exit-fee schedule, launch unit price, and maximum valuation age live on one versioned rule set, like rotation versions.

## Acceptance Criteria

- [ ] Represent fund share as integer basis points `0..10_000` and reject other values.
- [ ] Hold the partial-payment order as closed choices: penalty `penalty_first` (default), `penalty_last`, `pro_rata`; contribution `pot_first` (default), `pro_rata`.
- [ ] Hold the catch-up policy (allowed, deadline in cycles, default outcome `forfeit`), a per-exit-type fee percentage defaulting to 0 with death fixed at 0, a positive launch unit price, and a maximum valuation age.
- [ ] Apply one fee schedule to every unit; require a fee change to be adopted at least one full cycle before its effective cycle.
- [ ] Hold the declared legal form (`association`, `cooperative`, `unregistered`) and statute flags: unconditional right to refuse redemption, pro-rata distribution on wind-up, and uniform fee schedule.
- [ ] Reject an expulsion fee above the voluntary-exit fee when the legal form is `cooperative`; report it as a warning otherwise.
- [ ] Hold a payout deferral defaulting to cycle end, with at most 12 months by default and a hard ceiling of 24 months.
- [ ] Resolve the latest version effective for a cycle; reject a version whose effective cycle is not after the current cycle supplied by the caller.
- [ ] Allow an optional governance decision reference on each version.
- [ ] Reject currencies with no ISO 4217 minor unit.
- [ ] Tests cover resolution, ties, non-retroactivity, fee notice, cooperative expulsion-fee limits, deferral bounds, invalid values, and immutability.

## Planned Changes

- `src/tontine/hybrid/rules.py`
- `tests/hybrid/test_rules.py`

## Validation

```text
uv run pytest tests/hybrid
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Not started.
