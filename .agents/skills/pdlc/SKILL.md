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
- Preserve execution evidence in one completion record per shipped task.
- Use the bundled status roller to regenerate `docs/planning/STATUS.md` from
  capability and task frontmatter.

## Recommended structure

```text
docs/
  planning/
    requirements.md
    capabilities/
    tasks/
    completions/
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
- `templates/completion.md` for shipped-task evidence
- `templates/adr.md` for architecture or domain decisions
- `templates/status.md` for progress monitoring

Use `references/state-model.md` as the canonical reference for IDs, frontmatter,
status rollups, completion evidence, traceability, and ADR citations.
Use `references/traceability.md` for requirement coverage and wiring checks before
marking package behavior shipped.
Use `references/operating-model.md` for source-of-truth, delivery, roadmap, and
external-synchronization rules.

The stdlib-only status roller is at `scripts/status.py`; run it with `uv run
python .agents/skills/pdlc/scripts/status.py docs/planning`.

The stdlib-only ADR reverse index is at `scripts/adr_index.py`; run it with
`uv run python .agents/skills/pdlc/scripts/adr_index.py`.

The stdlib-only traceability checker is at `scripts/traceability.py`; run it with
`uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning`.

## Workflow

1. Read the relevant BRD section and identify the user or package behavior.
2. Add or reuse stable requirement IDs; never silently renumber existing IDs.
3. Define a capability and small, testable tasks with explicit acceptance criteria.
4. Implement domain behavior first, keeping adapters outside the core package.
5. Add focused tests for normal behavior, invalid transitions, duplicate events,
   money precision, and ledger-derived results.
6. Check every satisfied acceptance criterion with `[x]`; leave incomplete criteria
  unchecked and use `partial` or `blocked` instead of claiming completion.
7. Create `docs/planning/completions/TASK-<ID>.md` with dates, evidence, commands,
  changed files, and remaining gaps.
8. Update `started` and `completed` dates on the task and capability only when
  the evidence supports the status.
9. Recheck traceability so every requirement has a capability or task owner.
10. Record gaps, assumptions, and follow-up decisions for human review.

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

Every `shipped` task must have all acceptance criteria checked and a matching
completion record. A task with unchecked criteria cannot be `shipped`.

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
