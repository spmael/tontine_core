---
id: TASK-GOV-004
status: shipped
started: 2026-10-18
completed: 2026-10-18
requirements:
  - FR-GOV-005
  - FR-GOV-010
capability: CAP-GOV-002
adr_refs:
  - ADR-004
owner: domain
---

# Task: Add typed governance decision effects

## Goal

Support rotation and non-rotation proposal effects without executing arbitrary
proposal payloads.

## Context

The initial non-rotation effect is activation of an immutable `Ruleset`.
One-cycle rotation exceptions replace only the selected recipient and preserve
the base rotation.

## Acceptance Criteria

- [x] Represent rotation-order, one-cycle recipient-override, and ruleset
  activation effects with explicit domain types.
- [x] Create proposals for ruleset activation and one-cycle exceptions without
  requiring a full replacement rotation.
- [x] Apply an effect only after its proposal is approved.
- [x] Preserve the classic rotation base order and existing payout and
  unpaid-contribution rules outside the exception scope.
- [x] Test approved and rejected effects through the public governance API.

## Planned Changes

- `src/tontine/governance/`
- `tests/governance/`

## Validation

```text
uv run pytest tests/governance
uv run ruff check src/tontine/governance tests/governance
uv run mypy src/tontine/governance
```

## Completion Notes

This task follows the proposal policy and data types established by
`TASK-GOV-003`. Approved effects are audited and activated through
`GovernanceRegistry`; rejected effects leave the active rotation and rulesets
unchanged. One-cycle exceptions expose the unchanged base rotation together
with the selected recipient.
