# Traceability

Maintain a requirement -> capability -> task -> completion chain with no silent
orphans. Every `FR-*` and `NFR-*` in `docs/planning/requirements.md` must be
owned by at least one capability or task.

Run the stdlib-only checker after editing the requirements register or planning
frontmatter:

```text
uv run python .agents/skills/pdlc/scripts/traceability.py docs/planning
```

The checker reports:

- requirements with no capability or task owner;
- capability/task records citing an undefined requirement;
- coverage by requirement and planning file.

A non-zero result is a planning finding, not a reason to suppress the report or
invent a requirement. Resolve it by creating a capability/task, correcting a
reference, or documenting an explicit product decision.

## Wiring traceability

Requirement coverage answers: “Is every requirement represented in the plan?”
A separate check answers: “Can a real package consumer reach the implementation?”

A unit-tested function or class can still be orphaned if no public package API,
domain service, repository boundary, or explicitly planned adapter uses it. Tests
that call only the implementation directly do not prove that the capability is
usable.

A shipped task that adds production-facing behavior must do one of the following:

- **Prove the wiring:** add a test through the public package API or the real
  adapter boundary that will call the implementation in production.
- **Defer the wiring explicitly:** record why it is not wired, identify the future
  entry point, and use `partial` rather than `shipped`.

For the framework-independent core, “real entry point” means a documented public
Python API or domain boundary. A future UI, database adapter, payment adapter, or
web service is not assumed to exist unless it is explicitly planned and tested.

## Completion gate

Before marking a task or capability `shipped`, confirm:

1. Its requirement IDs are defined and covered.
2. Its acceptance criteria are checked with `[x]`.
3. Its tests exercise public behavior or document an intentional lower-level scope.
4. Its completion record names the validation commands and changed files.
5. Any missing production wiring is either proven or explicitly recorded as a
   residual gap with `partial` status.
