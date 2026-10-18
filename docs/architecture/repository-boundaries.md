# Repository Boundaries

`tontine-core` defines repository protocols at the domain boundary and supplies
small in-memory implementations for tests and examples.

## Public Error Contract

- Missing expected records raise `MissingRecordError`, a `TontineError` that is
  not a `KeyError`.
- Invalid values or state raise `ValueError`; values of the wrong Python type
  raise `TypeError`.
- More specific domain failures use the corresponding `TontineError` subclass
  where one is defined. Duplicate additions through repository `add()` methods
  raise `ValueError`.
- The core error hierarchy depends only on Python's built-in exception types.
  Framework and persistence adapters must translate their own boundary errors
  into this contract rather than introducing adapter-specific errors into the
  domain package.

## Semantics

- `add()` rejects duplicate stable identifiers with `ValueError`.
- `get()` raises `MissingRecordError` (a `TontineError`) for missing identifiers.
- `list()` returns deterministic stable-identifier order where applicable.
- Domain records remain responsible for their own immutability and invariants.
- Repository methods do not access networks, databases, payment providers, or
  financial institutions.

`MissingRecordError` is not a `KeyError`; callers should catch this documented
domain exception for expected missing-record failures. This is a breaking
change for callers that previously caught `KeyError`. Current protocols cover
groups, accounts, contribution cycles, ledger posting, and investment activity.
Future SQL, Django, SQLAlchemy, or other adapters must implement the same
protocols outside the core domain package.

## Naming Convention

- Protocols use the aggregate or boundary name: `LedgerRepository`,
  `MemberRepository`, and `AuditRepository`.
- Concrete in-memory implementations use the `InMemory` prefix:
  `InMemoryLedgerRepository` and `InMemoryMemberRepository`.
- Compatibility aliases may remain temporarily when an existing public import
  used the older name.
