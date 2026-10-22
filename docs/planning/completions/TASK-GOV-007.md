---
task: TASK-GOV-007
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-GOV-007

## Outcome

Added typed governance effects for member exits, penalty waivers, and reasoned
payout deferrals. Exit effects preserve the member, exit type, effective date,
and request cycle. Expulsion proposals exclude the subject, and waiver
proposals exclude the member named on the assessment. Payout deferrals require
an already approved exit, a reason, and a date more than 12 but no more than
24 calendar months after the exit takes effect.

Member decisions can be approved in the current cycle; cycle-effective rule and
rotation changes remain future-effective. Approved effects are auditable,
available by proposal identifier, and preserved with their electorate in
governance snapshots.

## Acceptance Criteria Evidence

- [x] A member-exit effect records member, exit type, exit date, and request
  cycle.
- [x] A penalty-waiver effect records the penalty assessment and assessed member.
- [x] A payout-deferral effect links to an approved exit and requires a reason
  and date within the 24-month ceiling.
- [x] Expulsion subjects and members whose own penalties are waived are absent
  from the frozen electorates.
- [x] Approved exit, waiver, and deferral effects are available through typed
  decision lookups.
- [x] Tests cover approval, rejection, recusal, electorate persistence,
  request-cycle provenance, deferral reasons and date boundaries, and snapshot
  restoration.

## Validation

```text
uv run pytest tests/governance/test_member_decisions.py -q
10 passed.

uv run pytest tests/governance -q
44 passed.

uv run ruff check src tests
All checks passed.

uv run ruff format --check src/tontine/governance tests/governance
13 files already formatted.

uv run mypy src
Success: no issues found in 37 source files.

uv run pytest -q
391 passed.

uv build -o /tmp/gov007-dist
Source distribution and wheel built successfully.

git diff --check
Passed.
```

The repository-wide `ruff format --check src tests` also reports nine files
outside the governance scope that would be reformatted. Those unrelated files
were left unchanged; all governance source and tests pass the scoped check.

## Files Changed

- `src/tontine/governance/models.py`
- `src/tontine/governance/_member_decisions.py`
- `src/tontine/governance/registry.py`
- `src/tontine/governance/__init__.py`
- `src/tontine/governance/snapshots.py`
- `src/tontine/governance/snapshot_validation.py`
- `tests/governance/test_member_decisions.py`
- `BRD.md`
- `docs/architecture/adr/ADR-004-governance-decision-lifecycle.md`
- `docs/planning/tasks/TASK-GOV-007.md`
- `docs/planning/capabilities/CAP-HYB-001.md`
- `docs/planning/STATUS.md`

## Gaps and Follow-up

The waiver effect retains the assessment identifier and member; validation
against an actual penalty assessment belongs with the penalty lifecycle in
TASK-HYB-005. This task records decisions only; exit settlement and external
payout handling remain in the subsequent hybrid work.
