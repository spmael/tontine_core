---
task: TASK-GOV-004
status: shipped
started: 2026-10-18
completed: 2026-10-18
---

# Completion: TASK-GOV-004

## Outcome

Governance proposals now carry explicit typed effects for base rotation changes,
one-cycle recipient overrides, and immutable ruleset activation. Registry
evaluation applies effects only after approval and records effect-specific audit
provenance. Rejected decisions leave rotations and rulesets unchanged.

## Acceptance Criteria Evidence

- [x] Public effect types validate their own scope and are re-exported from
  `tontine.governance`.
- [x] Public registry methods create exception and ruleset proposals without a
  replacement rotation order.
- [x] Approval applies rotation, exception, or ruleset effects; rejection
  applies none.
- [x] Rotation resolution returns the unchanged base rotation alongside the
  one-cycle selected recipient and approval event provenance.
- [x] Tests cover approved and rejected effects, duplicate pending exceptions,
  ruleset conflicts, and audit links using public APIs.

## Validation

```text
.venv/bin/python -m pytest tests/governance -q
.venv/bin/ruff check src/tontine/governance tests/governance
.venv/bin/mypy src/tontine/governance
.venv/bin/python -m pytest -q
.venv/bin/ruff check src tests
.venv/bin/mypy src
uv build
```

Results: 27 governance tests and 158 total tests passed; Ruff and mypy reported
no issues; source and wheel distributions built successfully.

## Files Changed

- `src/tontine/governance/models.py`
- `src/tontine/governance/registry.py`
- `src/tontine/governance/_lifecycle.py`
- `src/tontine/governance/__init__.py`
- `tests/governance/test_effects_and_snapshots.py`
- `BRD.md`
- `docs/planning/tasks/TASK-GOV-004.md`

## Gaps and Follow-up

No task-level gaps remain. Database and serialization adapters remain outside
the framework-independent core.
