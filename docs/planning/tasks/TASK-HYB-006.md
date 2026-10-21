---
id: TASK-HYB-006
status: shipped
started: 2026-10-18
completed: 2026-10-18
adr_refs:
  - ADR-006
requirements:
  - FR-HYB-004
capability: CAP-HYB-001
owner: domain
---

# Task: Record member exit and entitlement

## Goal

Settle an approved exit into an explicit entitlement or amount owed.

## Context

ADR-006 member exit, exit fee, death, and the deferral and heir rules researched under AUSCOOP and the Cameroonian Civil Code. Depends on TASK-HYB-005 and TASK-GOV-007. Unit classification stays a reporting concern (TASK-HYB-007).

## Acceptance Criteria

- [x] Record an exit event only from an approved exit decision; freeze units and block new issuance from the exit date.
- [x] Price at the first available valuation on or after the exit date; stay pending valuation until it exists.
- [x] Report lines in order: gross unit value, exit fee, unpaid dues and penalties, excess pot received; report a negative net as owed by the member.
- [x] Charge the fee version in force when the exit was requested, so an exit requested during a fee change's notice period keeps the old fee; record the fund as fee destination, and fix death at 0.
- [x] Hold a death entitlement for the estate until a proof-of-succession reference is recorded; move a disputed claim to `consigned` with a deposit or sequestration reference.
- [x] Record the payout as an entitlement deferred to the caller-supplied cycle-end date, with a liquidity-cap FIFO queue report; execute nothing.
- [x] Reject deferral beyond 12 months without an approved, reasoned deferral decision, and beyond 24 months in all cases.
- [x] Track payout status: `pending_valuation`, `queued`, `payable`, `held_for_estate`, `consigned`, and `paid_externally`; also distinguish `amount_owed` and `no_payout`.
- [x] Tests cover each exit type, pending and future valuations, offsets, negative nets, fees during notice, expulsion fee limits, deferral limits, consignment, and FIFO liquidity queues.

## Planned Changes

- `src/tontine/hybrid/exit.py`
- `src/tontine/hybrid/exit_models.py`
- `src/tontine/hybrid/_exit_calculations.py`
- `src/tontine/hybrid/arrears.py`
- `src/tontine/hybrid/allocation_registry.py`
- `src/tontine/hybrid/__init__.py`
- `tests/hybrid/test_exit.py`
- `tests/hybrid/test_arrears.py`

## Validation

```text
uv run pytest tests/hybrid
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Implemented approved exit recording, allocation freezing, forward-price
settlement, explicit arrears offsets, estate and consignment references, and
liquidity-limited FIFO entitlements. No payout is initiated by the package.
