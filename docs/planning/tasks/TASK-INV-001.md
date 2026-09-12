---
id: TASK-INV-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-INV-001
  - FR-INV-002
  - FR-INV-005
capability: CAP-INV-001
owner: domain
---

# Task: Define investment vocabulary and supplied FX rates

## Goal

Define investment allocation, asset, valuation, and externally supplied FX-rate
value objects using explicit Decimal amounts and currencies.

## Acceptance Criteria

- [x] Allocation categories use Decimal percentages and total exactly 100%.
- [x] Asset definitions require identifier, name, currency, and asset category.
- [x] Manual valuations require Decimal value, currency, effective date, and source.
- [x] FX rates require base currency, quote currency, Decimal rate, effective timestamp, and source.
- [x] FX rates are accepted as supplied data; no ECB or other network call exists in the core.
- [x] Tests cover JPY, XAF, EUR, USD, and fractional FX rates.

## Planned Changes

- `src/tontine/investments/`
- `tests/investments/`

## Validation

```text
uv run pytest tests/investments/test_investment_vocabulary.py
```

## Completion Notes

Implemented Decimal allocation rules, asset definitions, manual valuations, and timezone-aware externally supplied FX-rate records. ECB or another provider may be implemented later as an adapter that supplies validated records to the core.
