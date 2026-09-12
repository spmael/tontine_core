---
kind: status_dashboard
period: 2026-09-12
---

# Package Delivery Status

## Summary

- Backlog: 7 capabilities
- Ready: 3 capabilities
- In progress: 0 capabilities
- Blocked: 0 capabilities
- Partial: 0 capabilities
- Shipped: 0 capabilities

## In Progress

None. The package has a requirements register and a selected first vertical
slice; implementation has not started.

## Blocked

None currently. Technical choices that are intentionally open are recorded as
future architecture decisions rather than guessed here.

## Recent Planning Progress

- Planning foundation: BRD translated into 43 stable functional and
  non-functional requirements.
- Package foundation added as the first delivery item: `src/tontine/`,
  `tontine-core` distribution metadata, Python 3.12+ tooling, and smoke checks.
- First domain slice follows package bootstrap: group, membership, contribution
  rules, cycles, contribution status, and duplicate protection.
- Financial account registry included in Version 1 before ledger integration;
  account connectivity and custody remain excluded.

## Coverage Gaps

- Package foundation is planned but not implemented yet.
- No executable tests exist yet.
- Ledger, persistence interfaces, governance, reporting, and investment behavior
  remain unimplemented.
- Financial account registration and event linking remain unimplemented.

## Decisions Needed

- Decide whether to use Hatchling, Setuptools, or another PEP 517 build backend.
- Decide whether the initial type-checker should be Mypy or Pyright.
