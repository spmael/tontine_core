---
description: Audit requirement, capability, task, and completion coverage for the package.
argument-hint:
---

Run `uv run python .claude/skills/pdlc/scripts/traceability.py docs/planning`,
then read `docs/planning/requirements.md`, capability records, task records, and
completion records.

Report:

- requirements with no owning capability;
- capabilities with no linked requirements;
- tasks with no capability or requirement links;
- shipped tasks with missing completion records or unchecked criteria;
- completion records that reference missing tasks;
- identifiers cited in planning files but not defined in the register.

The command exits non-zero when uncovered requirements or undefined references
exist; report those findings rather than treating the non-zero result as a tool
failure.

Do not modify files during the check. Requirements and gaps must be reported for
human review rather than hidden by changing IDs.
