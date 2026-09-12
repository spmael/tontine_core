---
id: TASK-CLASSIC-002
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-CLS-002
  - FR-CLS-003
capability: CAP-CLASSIC-001
owner: domain
---

# Task: Record classic payouts

## Goal

Record immutable classic payout decisions with historical recipient provenance.

## Acceptance Criteria

- [x] Record recipient, cycle, amount, currency, and provenance.
- [x] Reject duplicate payouts for the same cycle.
- [x] Preserve historical recipient data after later rotation changes.
- [x] Add payout tests without initiating payment.

## Planned Changes

- `src/tontine/classic/`
- `tests/classic/`

## Validation

```text
uv run pytest tests/classic
```

## Completion Notes

Implemented immutable payout records with explicit Decimal amounts, currency, timezone-aware provenance, historical recipient data, and duplicate cycle protection.
