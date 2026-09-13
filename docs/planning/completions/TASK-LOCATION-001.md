---
task: TASK-LOCATION-001
status: shipped
started: 2026-09-13
completed: 2026-09-13
---

# Completion: TASK-LOCATION-001

## Outcome

Implemented optional ISO 3166-1 alpha-2 location metadata for groups and
members using the existing `CountryCode` value object.

## Acceptance Criteria Evidence

- [x] Optional group jurisdiction is validated and normalized through `Group.jurisdiction`.
- [x] Optional member residence country is validated and normalized through `Member.residence_country`.
- [x] Missing location metadata remains valid.
- [x] Location metadata does not perform KYC, identity verification, tax classification, or regulatory decisions.

## Validation

```text
uv run pytest tests/groups tests/members -q
uv run ruff check src/tontine/groups src/tontine/members tests/groups tests/members
uv run mypy src/tontine/groups src/tontine/members
```

Result: 16 tests passed; Ruff and mypy passed.

## Changed Files

- `src/tontine/countries/__init__.py` (reused existing validator)
- `src/tontine/groups/__init__.py`
- `src/tontine/members/__init__.py`
- `tests/groups/test_group_domain.py`
- `tests/members/test_membership.py`
- `BRD.md`
- `docs/planning/capabilities/CAP-LOCATION-001.md`
- `docs/planning/tasks/TASK-LOCATION-001.md`
