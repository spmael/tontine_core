# Operating Model

The package lifecycle is:

```text
BRD and planning markdown
  -> review
  -> status: ready
  -> implement with uv and tests
  -> checked acceptance criteria
  -> completion record
  -> status: shipped
```

## Source of truth

- `BRD_tontine_core_v1.md` is authoritative for product scope and Version 1 boundaries.
- `docs/planning/requirements.md` is authoritative for stable requirement IDs.
- Capability and task files are authoritative for scope and acceptance criteria.
- Completion records are authoritative for implementation evidence.
- `STATUS.md` and `CITATIONS.md` are generated reports, not planning inputs.

Do not duplicate acceptance criteria in an external issue or board. External tools
may link back to the planning file, but they must not become a second source of
scope or business rules.

## Local delivery flow

1. Read the BRD and linked requirement records.
2. Review the capability or task and confirm its dependencies.
3. Set a task to `in_progress` with its `started` date when implementation begins.
4. Implement the smallest testable change using the package boundaries.
5. Run the exact `uv run` validation commands in the task.
6. Check every satisfied acceptance criterion with `[x]`.
7. Create `docs/planning/completions/TASK-<ID>.md` with evidence and dates.
8. Mark the task `shipped` only when all evidence requirements pass.
9. Regenerate status and traceability reports.
10. Present the diff and proposed commit for human approval.

A task can be completed entirely within the repository. No external issue or
project board is required for delivery.

## Status and reconciliation

Planning frontmatter is authoritative. If an external tracker is later used and
its status disagrees with the repository, reconcile from the planning file rather
than hand-editing the tracker as a new source of truth.

Run:

```text
uv run python .claude/skills/pdlc/scripts/status.py docs/planning
uv run python .claude/skills/pdlc/scripts/traceability.py docs/planning
uv run python .claude/skills/pdlc/scripts/adr_index.py
```

The traceability command may exit non-zero when requirements are intentionally
uncovered. Treat its report as a planning finding and resolve it explicitly.

## External issue tracking

There is no configured GitHub repository or project board for `tontine-core` in
this workflow. `/pdlc:issues-sync` is dry-run only until a repository target,
permissions, labels, and ownership model are explicitly approved.

If external synchronization is enabled later:

- sync only when explicitly requested for a named task or capability;
- keep the planning file as the scope and acceptance source;
- make synchronization idempotent;
- never send credentials, account references, financial data, or secrets;
- report created, updated, skipped, and failed records;
- require confirmation before creating or mutating external issues.

## Roadmap planning

The local roadmap is organized by package capability, not by application or
external iteration board. A roadmap review should report:

- capability dependency order;
- ready, active, blocked, partial, and shipped work;
- actual `started` and `completed` dates for shipped work;
- assumptions behind future sequencing;
- decisions needed from the project owner.

Do not invent precise estimates for financial or governance work. Use a checkpoint
or range and record the assumption in the planning file or an ADR.

## Architecture decisions

Create ADRs under `docs/architecture/adr/` for decisions that affect package
boundaries, ledger semantics, account registration, ownership calculations,
framework adapters, or public API compatibility.

Use `adr_refs: []` on capabilities and tasks when they depend on a decision. Run
the ADR reverse index after changing citations:

```text
uv run python .claude/skills/pdlc/scripts/adr_index.py
```

## Package safety boundary

The operating model must preserve these Version 1 boundaries:

- no payment custody or transfer initiation;
- no bank, broker, or market-data connections;
- no credentials or secrets in planning records;
- no framework dependency in the domain package;
- no silent financial-rule changes;
- no shipped status without executable validation and completion evidence.
