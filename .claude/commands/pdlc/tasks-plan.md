---
description: Plan small implementation tasks for a package capability.
argument-hint: <capability file path>
---

Follow the `pdlc` skill and `templates/task.md`. Capability: `$ARGUMENTS`.

1. Read the capability, linked requirements, BRD sections, and existing tasks.
2. Identify the smallest implementation tasks needed to satisfy its acceptance
   criteria.
3. Give each task a stable `TASK-<DOMAIN>-NNN` ID, requirements, capability,
   owner, status, `started`, and `completed` fields.
4. Include testable acceptance criteria, planned files, and exact `uv run`
   validation commands.
5. Keep domain behavior separate from adapters and avoid inventing rules absent
   from the BRD.
6. Present the task plan for review before changing a task to `in_progress`.
