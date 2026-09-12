# Repository Boundaries

`tontine-core` defines repository protocols at the domain boundary and supplies
small in-memory implementations for tests and examples.

## Semantics

- `add()` rejects duplicate stable identifiers with `ValueError`.
- `get()` raises `KeyError` for missing identifiers.
- `list()` returns deterministic stable-identifier order where applicable.
- Domain records remain responsible for their own immutability and invariants.
- Repository methods do not access networks, databases, payment providers, or
  financial institutions.

Current protocols cover groups, accounts, contribution cycles, ledger posting,
and investment activity. Future SQL, Django, SQLAlchemy, or other adapters must
implement the same protocols outside the core domain package.

## Naming Convention

- Protocols use the aggregate or boundary name: `LedgerRepository`,
  `MemberRepository`, and `AuditRepository`.
- Concrete in-memory implementations use the `InMemory` prefix:
  `InMemoryLedgerRepository` and `InMemoryMemberRepository`.
- Compatibility aliases may remain temporarily when an existing public import
  used the older name.
