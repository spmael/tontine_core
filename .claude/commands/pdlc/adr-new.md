---
description: Create an architecture decision record for tontine-core.
argument-hint: <short decision title>
---

Create `docs/architecture/adr/ADR-NNN-<slug>.md` from
`.claude/skills/pdlc/templates/adr.md` for: `$ARGUMENTS`.

1. Create `docs/architecture/adr/` if needed.
2. Choose the next unused numeric ADR ID.
3. Record context, decision, alternatives, consequences, and verification.
4. Add `started` and `completed` dates when the decision is finalized.
5. Add an `adr_refs: []` field to affected capability/task frontmatter only after
   confirming which records depend on the decision.
6. Run `uv run python .claude/skills/pdlc/scripts/adr_index.py` to regenerate the
   reverse citation index.
7. Keep the decision consistent with framework independence, ledger traceability,
   explicit currency units, and Version 1 exclusions.
8. Do not silently change the BRD or task status; identify affected records for
   review.
