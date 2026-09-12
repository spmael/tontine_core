---
description: Execute one tontine-core task with tests, checked acceptance criteria, and a completion record.
argument-hint: <task file path>
---

Follow the `pdlc` and `python-standards` skills. Task: `$ARGUMENTS`.

1. Read the task, linked capability, requirements, and relevant BRD sections.
2. Set the task to `in_progress` and record `started: YYYY-MM-DD`.
3. Work test-first where practical: add or update focused tests, implement the
   smallest change, and preserve framework independence.
4. Run the task validation commands with `uv run` and any relevant package checks.
5. Check every satisfied acceptance criterion with `[x]`; leave incomplete items
   unchecked.
6. Create `docs/planning/completions/TASK-<ID>.md` using the completion template.
   Include started/completed dates, evidence, commands, files, and remaining gaps.
7. Mark the task `shipped` only when every criterion is checked and validation
   passes. Otherwise use `partial` or `blocked` and explain why.
8. Update the capability status only after all child tasks are verified. Do not
   commit automatically; present the diff and proposed commit message for review.
