---
id: TASK-ACCOUNT-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
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

- [x] Support cash, bank, microfinance, mobile wallet, broker, and other account types.
- [x] Require explicit currency and institution metadata where applicable.
- [x] Store only masked account references.
- [x] Reject credentials, secrets, and unmasked account identifiers.
- [x] Add concise public docstrings and invariant-focused tests.

## Planned Changes

- `src/tontine/accounts/`
- `src/tontine/exceptions.py`
- `tests/accounts/`

## Validation

```text
python -m pytest tests/accounts
```

## Completion Notes

Implemented immutable financial account records with explicit type, currency, status, institutional metadata, and conservative masked-reference validation. No credentials or external-access operations are represented.
