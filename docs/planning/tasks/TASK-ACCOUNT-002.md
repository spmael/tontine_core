---
id: TASK-ACCOUNT-002
status: backlog
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

- [ ] A financial event can reference a registered account by identifier.
- [ ] References are validated against the account registry.
- [ ] Missing or inactive account references are handled explicitly.
- [ ] No network, bank, broker, payment, or live-balance operation is introduced.
- [ ] Tests prove event reconstruction from recorded references.

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

Not started.
