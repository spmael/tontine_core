---
id: TASK-INV-005
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-INV-005
capability: CAP-INV-001
owner: domain
---

# Task: Add external FX adapter boundary

## Goal

Allow external providers such as ECB reference-rate feeds to supply FX records
without coupling the core investment domain to HTTP, credentials, or schedules.

## Acceptance Criteria

- [x] Define a provider-neutral FX-rate source protocol at the adapter boundary.
- [x] Accept validated rate records containing source, timestamp, base, quote, and rate.
- [x] Keep ECB/client/network code outside `src/tontine/investments/` core entities.
- [x] Reject stale, missing, inverted, or invalid rates according to explicit policy.
- [x] Add adapter contract tests using fixture data rather than live network calls.

## Planned Changes

- `src/tontine/investments/`
- `src/tontine/adapters/`
- `tests/investments/`
- `tests/adapters/`

## Validation

```text
uv run pytest tests/investments tests/adapters
```

## Completion Notes

Implemented `FxRateSource` as a provider-neutral protocol and explicit freshness validation for supplied rates. ECB remains a future external adapter; no network code is present in the core.
