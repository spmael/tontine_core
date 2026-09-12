---
name: pdlc
description: >-
  Project development lifecycle workflow for tontine-core. Use when planning,
  decomposing, implementing, monitoring, auditing, or reviewing package work;
  maintaining requirements traceability; or checking progress against the BRD.
user_invocable: true
---

# Package Development Lifecycle

Use this skill to keep implementation work connected to the product requirements
in `BRD_tontine_core_v1.md`. The package is the unit of delivery; organize work by
domain capability, not by web application or framework.

## Responsibilities

- Maintain a requirements register with stable `FR-*` and `NFR-*` identifiers.
- Break requirements into domain-oriented capabilities and implementation tasks.
- Keep each task linked to its requirement, acceptance criteria, tests, and status.
- Monitor progress from backlog through ready, in progress, blocked, partial, and shipped.
- Record design decisions and unresolved assumptions instead of hiding them in code.
- Audit the real package and tests, not only planning documents.

## Recommended structure

```text
docs/
  planning/
    requirements.md
    capabilities/
    tasks/
    STATUS.md
  architecture/
    adr/
```

Create this structure only when the project begins formal planning; the BRD remains
the source of truth until then.

Use the templates bundled with this skill:

- `templates/requirement.md` for functional and non-functional requirements
- `templates/capability.md` for domain capabilities
- `templates/task.md` for implementation work
- `templates/adr.md` for architecture or domain decisions
- `templates/status.md` for progress monitoring

## Workflow

1. Read the relevant BRD section and identify the user or package behavior.
2. Add or reuse stable requirement IDs; never silently renumber existing IDs.
3. Define a capability and small, testable tasks with explicit acceptance criteria.
4. Implement domain behavior first, keeping adapters outside the core package.
5. Add focused tests for normal behavior, invalid transitions, duplicate events,
   money precision, and ledger-derived results.
6. Verify the task against its acceptance criteria and update its status.
7. Recheck traceability so every requirement has a capability or task owner.
8. Record gaps, assumptions, and follow-up decisions for human review.

## Status rules

Use only these statuses:

- `backlog`: identified but not prepared for implementation
- `ready`: acceptance criteria and dependencies are clear
- `in_progress`: actively being implemented
- `blocked`: cannot proceed without an external decision or dependency
- `partial`: some acceptance criteria are complete
- `shipped`: implemented and verified

Never mark work `shipped` without executable validation. Unknown dates and explicit
open questions are preferable to invented certainty.

## Domain review checklist

- Does the change preserve framework independence?
- Are balances, ownership, NAV, and statements derived from ledger events?
- Are currency, amount units, rounding, and valuation inputs explicit?
- Are governance changes and financially meaningful events auditable?
- Does the change stay within Version 1 exclusions, especially no custody or payment execution?
- Are public APIs and domain errors documented and tested?

## Monitoring output

A progress review should report:

- shipped work since the previous review;
- active and blocked work;
- uncovered or weakly covered requirements;
- test or documentation gaps;
- decisions needed from the project owner.

Do not modify requirements to make implementation appear complete. Record a gap and
ask for a product decision.
