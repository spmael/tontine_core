---
id: TASK-MEM-002
status: shipped
started: 2026-10-21
completed: 2026-10-21
adr_refs:
  - ADR-008
requirements:
  - FR-MEM-001
capability: CAP-MEM-001
owner: domain
depends_on:
  - TASK-MEM-001
---

# Task: Integrate share-level obligations and reporting

## Goal

Use stable participation share identifiers for cycle contributions and rotation
positions while retaining person-level governance and reporting roll-ups.

## Context

ADR-008 uses share IDs as participant keys where domain rules operate per share.
Governance proposal eligibility remains keyed by member ID.

## Acceptance Criteria

- [x] Allow expected and received cycle contributions to be recorded per active
  share without losing the owning member identity.
- [x] Allow classic rotation positions to reference shares and resolve recipients
  to the owning member for payout and person-level governance boundaries.
- [x] Aggregate share-level contribution and rotation reporting by person without
  double-counting.
- [x] Preserve existing member-keyed APIs and recorded rotation versions.
- [x] Test multiple shares per person, invalid share/cycle references, roll-up,
  and one-vote-per-member behavior.

## Planned Changes

- `src/tontine/contributions/`
- `src/tontine/classic/`
- `src/tontine/members/participation.py` for ownership resolution and exact
  same-currency roll-up
- focused contribution, rotation, and reporting tests

## Validation

```text
uv run pytest tests/contributions tests/classic tests/reporting tests/members
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Shipped under ADR-008. Contribution cycles accept active share records and return
owner-aware wrappers; classic rotation versions retain share IDs while schedule
resolution can return the owning member. Same-currency Decimal amounts roll up
per member and never combine different currencies.
