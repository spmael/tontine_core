---
id: TASK-ACCOUNT-003
status: backlog
requirements:
  - FR-ACC-001
  - FR-ACC-002
  - NFR-ACC-001
  - NFR-TEST-001
capability: CAP-ACCOUNT-001
owner: domain
---

# Task: Test and document account registration

## Goal

Document the difference between recording an external account and connecting to
one, with tests that protect the Version 1 boundary.

## Acceptance Criteria

- [ ] Examples show a masked bank or cash account reference.
- [ ] Tests prove credentials and live-access operations are not part of the API.
- [ ] Account-to-ledger mapping is documented.
- [ ] The README explains that real money remains with external institutions.

## Planned Changes

- `README.md`
- `examples/`
- `tests/accounts/`

## Validation

```text
python -m pytest tests/accounts
```

## Completion Notes

Not started.
