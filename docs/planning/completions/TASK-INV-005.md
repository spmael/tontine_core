---
task: TASK-INV-005
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-INV-005

Implemented provider-neutral `FxRateSource` and explicit rate freshness validation. ECB remains an external adapter concern; no network client is in the core. Validation is covered by `tests/investments/test_fx_boundary.py`.
