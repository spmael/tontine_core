# Package Planning State Model

This repository plans and delivers a Python package. The planning unit is a
package capability and its implementation tasks, not a UI or framework module.

## Planning records

The planning tree is:

```text
docs/planning/
  requirements.md
  capabilities/
  tasks/
  completions/
  STATUS.md
```

- `requirements.md` is the package-wide requirements register and source for
  stable `FR-*` and `NFR-*` identifiers.
- A capability describes a domain boundary and owns implementation tasks.
- A task is a small, testable unit of implementation.
- A completion record preserves evidence for a shipped task.
- `STATUS.md` is generated from capability and task frontmatter.

## Identity

- Requirement IDs are namespaced by domain, for example `FR-GRP-001`,
  `FR-CON-001`, and `NFR-CAL-001`.
- Capability IDs use `CAP-<DOMAIN>-NNN`, for example `CAP-GROUP-001`.
- Task IDs use `TASK-<DOMAIN>-NNN`, for example `TASK-GROUP-001`.
- Completion records use the matching task ID, for example
  `completions/TASK-GROUP-001.md`.
- ADRs use `ADR-NNN` and may be cited by capability or task `adr_refs`.

IDs are stable. Do not renumber or reuse an existing ID because a requirement,
capability, or task was changed or completed.

## Frontmatter

Capabilities and tasks should include:

```yaml
id: CAP-GROUP-001
status: ready
started: null
completed: null
requirements:
  - FR-GRP-001
adr_refs: []
owner: domain
```

Tasks additionally include `capability: CAP-GROUP-001`. Requirements include
`kind`, `status`, `started`, `completed`, and `owner`.

Dates are ISO `YYYY-MM-DD`. Use `null` until work starts or completes; do not
invent dates.

## Status vocabulary

The canonical statuses are:

```text
backlog | ready | in_progress | shipped | partial | blocked
```

- `backlog`: identified but not prepared for implementation.
- `ready`: acceptance criteria and dependencies are clear.
- `in_progress`: actively being implemented.
- `shipped`: all acceptance criteria are checked and validation passes.
- `partial`: some criteria are complete, with a documented residual gap.
- `blocked`: work cannot proceed because of an external dependency or decision.

Unknown values are vocabulary drift and must be reported by the status roller.
Do not silently map an unknown value to a known status.

## Completion and acceptance evidence

A task may be `shipped` only when:

1. Every satisfied acceptance criterion is checked with `- [x]`.
2. No incomplete criterion remains hidden in prose.
3. `started` and `completed` dates are present.
4. Executable validation has passed.
5. `docs/planning/completions/TASK-<ID>.md` exists.
6. The completion record lists evidence, commands, changed files, and remaining gaps.

A capability may be `shipped` only when its child tasks are shipped and its own
acceptance criteria are checked. A task or capability with a known residual gap
must be `partial`, not `shipped`.

## Rollup rule

The status roller reports capability and task statuses independently. A human
must confirm rollups:

- A capability is `shipped` only when every child task is `shipped` and the
  capability acceptance criteria are checked.
- A package milestone is complete only when all capabilities in its scope are
  shipped.
- `partial` and `blocked` never count as shipped.

## Requirements traceability

`traceability.py` reads `docs/planning/requirements.md` and compares its IDs with
`requirements:` in capability and task frontmatter. It reports:

- requirements with no capability or task owner;
- references to undefined requirements;
- capability/task records without valid requirement links.

Uncovered requirements are planning findings, not permission to invent code or
rewrite the BRD.

## ADR citations

Capabilities and tasks may use `adr_refs: []` to cite decisions in
`docs/architecture/adr/`. `adr_index.py` generates the reverse index at
`docs/architecture/adr/CITATIONS.md`.

The BRD and planning markdown remain authoritative. Generated dashboards and ADR
indexes are reports and must not be hand-edited.

## Package boundaries

Planning must preserve the core package boundaries:

- Domain behavior remains framework-independent.
- Ledger-derived balances, ownership, NAV, and statements remain the source of truth.
- Currency, amount units, rounding, and valuation inputs are explicit.
- Account registration records context but never enables custody or payment execution.
- UI, persistence adapters, authentication, external integrations, and GitHub
  synchronization remain outside the core unless explicitly added as a later capability.
