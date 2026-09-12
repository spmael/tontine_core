---
id: TASK-REPORT-003
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-RPT-001
  - FR-RPT-002
  - FR-RPT-003
capability: CAP-REPORT-001
owner: reporting
---

# Task: Add contribution and investment summary projections

## Goal

Expose deterministic contribution-status and investment-summary projections
from existing domain records.

## Acceptance Criteria

- [x] Project member contribution history and outstanding status.
- [x] Project group expected, received, and outstanding contribution totals.
- [x] Project investment assets, liabilities, NAV, units, and ownership values.
- [x] Preserve Decimal arithmetic, explicit currencies, dates, and provenance.
- [x] Add tests for empty, partial, and complete source data.

## Planned Changes

- `src/tontine/reporting/`
- `tests/reporting/`

## Validation

```text
uv run pytest tests/reporting/test_summary_projections.py
```

## Completion Notes

Reporting builders consume supplied domain records and preserve Decimal arithmetic without maintaining independent financial balances.
