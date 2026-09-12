---
id: TASK-LOCATION-001
status: backlog
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

- [ ] Add reusable ISO 3166-1 alpha-2 validation for optional location fields.
- [ ] Add optional group jurisdiction metadata.
- [ ] Add optional member residence-country metadata.
- [ ] Test missing, valid, and invalid location values.
- [ ] Document that the fields do not perform KYC, tax, or regulatory checks.

## Planned Changes

- `src/tontine/locations/`
- `src/tontine/groups/`
- `src/tontine/members/`
- `tests/locations/`

## Validation

```text
uv run pytest tests/locations tests/groups tests/members
```

## Completion Notes

Backlog item. Country metadata is intentionally optional and separate from the
core group and member identity requirements.