---
id: TASK-ACCOUNT-001
status: backlog
requirements:
  - FR-ACC-001
  - NFR-ACC-001
capability: CAP-ACCOUNT-001
owner: domain
---

# Task: Define financial account records

## Goal

Create a framework-independent financial account record that identifies where
money or assets are held without storing credentials or enabling access.

## Acceptance Criteria

- [ ] Support cash, bank, mobile wallet, broker, and other account types.
- [ ] Require explicit currency and institution metadata where applicable.
- [ ] Store only masked account references.
- [ ] Reject credentials, secrets, and unmasked account identifiers.
- [ ] Add concise public docstrings and invariant-focused tests.

## Planned Changes

- `src/tontine/accounts/`
- `src/tontine/exceptions.py`
- `tests/accounts/`

## Validation

```text
python -m pytest tests/accounts
```

## Completion Notes

Not started.
