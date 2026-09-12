---
description: Review package lifecycle status, dates, acceptance evidence, and completion records.
argument-hint:
---

Run `uv run python .claude/skills/pdlc/scripts/status.py docs/planning` to regenerate
the dashboard, then review `docs/planning/` and report:

1. Counts of capabilities and tasks by `backlog`, `ready`, `in_progress`,
   `blocked`, `partial`, and `shipped`.
2. Any shipped task missing `started`, `completed`, checked acceptance criteria,
   or `docs/planning/completions/TASK-<ID>.md`.
3. Work currently in progress or blocked, including the next checkpoint.
4. Recently shipped work and its executable validation evidence.
5. Requirements without a capability or task owner.
6. Decisions, gaps, or stale dates needing project-owner attention.

Do not mark or repair status silently. Present proposed corrections for review.
