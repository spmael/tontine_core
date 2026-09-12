---
id: TASK-INV-003
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-INV-003
capability: CAP-INV-001
owner: domain
---

# Task: Calculate NAV and member ownership

## Goal

Derive total assets, liabilities, NAV, unit price, and member attributable value
from recorded investment and ledger data.

## Acceptance Criteria

- [x] Calculate total assets using Decimal arithmetic.
- [x] Calculate total liabilities using Decimal arithmetic.
- [x] Calculate `NAV = assets - liabilities`.
- [x] Calculate unit price from NAV and units outstanding.
- [x] Derive member attributable value from units and unit price.
- [x] Add tests for fractional EUR and whole-unit JPY/XAF values.

## Planned Changes

- `src/tontine/investments/`
- `tests/investments/`

## Validation

```text
uv run pytest tests/investments/test_valuation.py
```

## Completion Notes

Implemented Decimal-based NAV, unit-price, and member-attributable-value calculations from supplied valuation inputs without implicit currency quantization.
