---
id: TASK-LOCATION-001
status: shipped
started: 2026-09-13
completed: 2026-09-13
requirements:
  - FR-LOC-001
  - FR-LOC-002
capability: CAP-LOCATION-001
owner: domain
---

# Task: Add optional location metadata

## Goal

Add optional, ISO-validated location metadata without making country part of the
required group or member identity model.

## Acceptance Criteria

- [x] Add reusable ISO 3166-1 alpha-2 validation for optional location fields.
- [x] Add optional group jurisdiction metadata.
- [x] Add optional member residence-country metadata.
- [x] Test missing, valid, and invalid location values.
- [x] Document that the fields do not perform KYC, tax, or regulatory checks.

## Planned Changes

- `src/tontine/groups/`
- `src/tontine/members/`
- `src/tontine/countries/`
- `tests/groups/`
- `tests/members/`

## Validation

```text
uv run pytest tests/groups tests/members
```

## Completion Notes

Implemented using the existing `CountryCode` value object. Country metadata is
optional and separate from identity verification, tax, and regulatory behavior.

Validation: `uv run pytest tests/groups tests/members -q`, with 16 tests passing;
Ruff and mypy passed for the changed modules.