---
description: Audit tontine-core architecture, domain boundaries, tests, and delivery evidence.
argument-hint: [scope]
---

Audit the requested scope, or the whole package if omitted.

Review:

- framework independence and adapter boundaries;
- ledger source-of-truth design;
- currency, Decimal, rounding, and valuation rules;
- account registry and no-custody boundary;
- public API and docstring quality;
- test coverage for invalid transitions and duplicate events;
- planning traceability, checked criteria, dates, and completion records.

Write findings to `docs/planning/audits/YYYY-MM-DD-package-audit.md` and report
Critical, At risk, Formalize, and Solid findings. Do not create tasks automatically;
ask for approval before turning a finding into planned work.
