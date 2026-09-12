---
description: Map BRD requirements to package capabilities.
argument-hint:
---

This package uses capabilities rather than application epics. Read the BRD and
`docs/planning/requirements.md`, then update `docs/planning/capabilities/`.

1. Group requirements by domain boundary such as package foundation, group,
   contributions, accounts, ledger, governance, investments, and reporting.
2. Use `CAP-<DOMAIN>-NNN` identifiers and the capability template.
3. Define outcomes, invariants, exclusions, acceptance criteria, tasks, dates,
   and verification.
4. Do not mark a capability shipped until all child tasks have checked criteria
   and completion records.
5. Present the proposed capability map before creating new capabilities.
