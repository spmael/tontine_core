---
task: TASK-GOV-001
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-GOV-001

## Outcome

Implemented versioned rulesets, vote-approved rotation proposals, deterministic thresholds, effective-cycle activation, and append-only governance audit events.

## Acceptance Criteria Evidence

- [x] Proposals include proposer, candidate rotation, deadline, threshold, and effective cycle.
- [x] Eligible members cast one vote using yes, no, or abstain.
- [x] Approval is calculated as yes votes divided by eligible members against the explicit percentage threshold.
- [x] Approved rotations become effective at the configured cycle and do not mutate earlier rotations.
- [x] Proposal, vote, evaluation, rotation, and ruleset events retain audit provenance.

## Validation

```text
uv run pytest tests/governance/test_governance.py && uv run ruff check src/tontine/governance tests/governance && uv run mypy src/tontine/governance
```

Result: 4 tests passed; Ruff and mypy passed.

## Files Changed

- `src/tontine/governance/__init__.py`
- `tests/governance/test_governance.py`
- `src/tontine/exceptions.py`
- `docs/planning/tasks/TASK-GOV-001.md`

## Gaps and Follow-up

Authentication, external signatures, and regulatory decisions remain outside the core governance boundary.