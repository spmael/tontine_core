---
id: TASK-ACCOUNT-002
status: shipped
started: 2026-09-12
completed: 2026-09-12
requirements:
  - FR-ACC-002
  - NFR-ACC-001
capability: CAP-ACCOUNT-001
owner: domain
---

# Task: Link account records to financial events

## Goal

Allow recorded contributions, payouts, cash movements, and investment
transactions to reference a registered financial account without external access.

## Acceptance Criteria

- [x] A financial event can reference a registered account by identifier.
- [x] References are validated against the account registry.
- [x] Missing or inactive account references are handled explicitly.
- [x] No network, bank, broker, payment, or live-balance operation is introduced.
- [x] Tests prove event reconstruction from recorded references.

## Planned Changes

- `src/tontine/accounts/`
- `src/tontine/ledger/`
- `tests/accounts/`
- `tests/ledger/`

## Validation

```text
python -m pytest tests/accounts tests/ledger
```

## Completion Notes

Implemented in-memory account registration, active-account event references, logical ledger-account links, duplicate protection, and deterministic reconstruction without network or financial-institution access.
