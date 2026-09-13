---
description: Project conventions for tontine-core
alwaysApply: true
---

# tontine-core Working Conventions

`tontine-core` is a framework-independent Python library for community tontines,
rotating savings groups, and investment clubs. Version 1 supports classic rotating
payouts and investment allocation tracking without holding or moving real funds.

## Source of truth

Read [`BRD.md`](./BRD.md) before proposing domain
or architectural changes. It defines the Version 1 scope, users, domain model,
and explicit exclusions.

## Architecture

- Keep the core independent of Django, Flask, FastAPI, databases, payment providers, and market-data feeds.
- Organize code by capability, such as `tontine/`, `ledger/`, `governance/`, and `reporting/`.
- Keep adapters at the boundary and prevent persistence concerns from leaking into the domain layer.
- Preserve public imports through package `__init__.py` files when modules split.

## Domain rules

- Treat the ledger as the source of truth. Derive balances, ownership, NAV, and statements from recorded transactions.
- Keep financially meaningful events, rule changes, proposals, votes, and valuation inputs traceable.
- Make currency and amount units explicit at public boundaries.
- Keep custody, payment initiation, lending, tax, KYC/AML, and automated investment execution out of Version 1.
- Prefer immutable value objects and explicit state transitions over mutable balance fields and hidden side effects.

## Python

- Follow the standalone `python-standards` skill for concise docstrings, short
	purposeful comments, typing, tests, and financial calculation conventions.
- Use Google-style docstrings for public APIs, including `Args`, `Returns`, and `Raises` where applicable.
- Public finance and calculation APIs must state units and cite the governing formula or business rule when one exists.
- Keep files below roughly 500 lines; split by domain capability when they grow.
- Add focused tests for invariants, invalid transitions, duplicate events, and rounding or currency behavior.

## Tooling

- Use the `pdlc` skill for package planning, requirements traceability, progress monitoring, and implementation audits. Create `docs/planning/` when formal tracking begins.
- `.audit/` is optional browser tooling for a separately configured web adapter; this repository itself is a library and has no default web server.

## Do-not-ship checklist

1. No payment custody or external fund movement has entered the core package.
2. Ledger-derived values do not depend on manually maintained balances.
3. Rule changes and financially meaningful events remain auditable.
4. Framework adapters do not leak into the domain layer.
5. Generated dependencies, screenshots, local settings, credentials, and nested worktrees are not committed.
