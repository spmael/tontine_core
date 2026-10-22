---
task: TASK-GOV-003
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-GOV-003

## Outcome

Governance proposals now freeze their electorate and current-cycle context,
apply an explicit quorum and abstention policy, enforce deadline/evaluation
boundaries, and retain immutable tally results with evaluation outcomes. All
mutating governance operations require explicit timezone-aware occurrence times.

## Acceptance Criteria Evidence

- [x] `RotationProposal` retains a sorted electorate snapshot, cycle context,
  quorum ratio, opened time, votes, and evaluation result.
- [x] `ProposalTally` exposes eligible, yes, no, abstain, non-voting,
  participation, quorum, and threshold results.
- [x] The two-thirds quorum uses integer ceiling; abstentions count toward
  quorum but not yes votes. Zero quorum preserves threshold-only behavior.
- [x] Votes at the deadline are accepted; votes after it are rejected. Early
  evaluation requires all eligible members to have voted.
- [x] Proposals require an effective cycle greater than caller-supplied current
  cycle. Membership changes do not rewrite existing electorates.
- [x] Tests cover explicit times, timezone validation, membership changes,
  deadline boundaries, quorum, and invalid lifecycle transitions.

## Validation

```text
uv run pytest tests/governance/test_governance.py tests/governance/test_proposal_policies.py
uv run ruff check src/tontine/governance tests/governance
uv run mypy src/tontine/governance
```

Results: 18 governance tests passed; Ruff and mypy reported no issues.

## Files Changed

- `src/tontine/governance/__init__.py`
- `src/tontine/governance/models.py`
- `src/tontine/governance/registry.py`
- `tests/governance/test_governance.py`
- `tests/governance/test_proposal_policies.py`
- `docs/architecture/adr/ADR-004-governance-decision-lifecycle.md`
- `docs/planning/capabilities/CAP-GOV-002.md`
- `docs/planning/tasks/TASK-GOV-003.md`
- `docs/planning/completions/TASK-GOV-003.md`

## Gaps and Follow-up

- Typed approval effects and versioned snapshot/rehydration behavior are
  tracked by `TASK-GOV-004` and `TASK-GOV-005`.
