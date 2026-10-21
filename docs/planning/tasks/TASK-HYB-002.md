---
id: TASK-HYB-002
status: shipped
started: 2026-10-18
completed: 2026-10-18
adr_refs:
  - ADR-006
requirements:
  - FR-HYB-001
capability: CAP-HYB-001
owner: domain
---

# Task: Split a received contribution into pot and fund

## Goal

Provide a pure split of an amount received into pot and fund shares.

## Context

ADR-006: `fund = round_down(received * bps / 10_000)` to the smallest currency unit and `pot = received - fund`; this is an explicit posting rounding under ADR-001. Depends on TASK-HYB-001.

## Acceptance Criteria

- [x] Split the amount received, never the expected amount.
- [x] Round the fund share down to the currency's smallest unit; derive the pot as the remainder.
- [x] A Hypothesis property test proves pot + fund == received for any basis-point value (`0..10_000`) and any valid XAF or EUR amount, with explicit examples for 0 bps, 10_000 bps, and the smallest currency unit.
- [x] Reject negative and non-finite amounts and amounts below the smallest currency unit.
- [x] Document units, rounding, and the governing rule in the public docstring.

## Planned Changes

- `src/tontine/hybrid/split.py`
- `tests/hybrid/test_split.py`
- `pyproject.toml`: add `hypothesis` to the `dev` dependency group only

## Validation

```text
uv run pytest tests/hybrid
uv run ruff check src tests
uv run mypy src
```

## Completion Notes

Implemented and verified on 2026-10-18; see
[completion evidence](../completions/TASK-HYB-002.md). Hypothesis is a
development-only dependency. The split returns `(pot, fund)` amounts and
performs no posting, allocation, or unit issuance.
