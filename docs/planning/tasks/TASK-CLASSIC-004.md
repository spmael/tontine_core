---
id: TASK-CLASSIC-004
status: backlog
requirements:
  - FR-CLS-001
  - FR-CLS-002
capability: CAP-CLASSIC-001
owner: domain
---

# Task: Add auditable randomized rotation

## Goal

Allow a classic tontine to generate its recipient order once using a reproducible,
auditable randomization process.

## Acceptance Criteria

- [ ] Generate a rotation from a supplied active-member set and explicit seed.
- [ ] Persist the seed, algorithm/version, input member set, generated order, actor, and timestamp.
- [ ] Never randomize again during recipient lookup.
- [ ] Reconstruct the same order from recorded randomization provenance.
- [ ] Add tests for reproducibility and historical reconstruction.

## Planned Changes

- `src/tontine/classic/`
- `tests/classic/`

## Validation

```text
uv run pytest tests/classic/test_random_rotation.py
```

## Completion Notes

Backlog item. The current V1 implementation remains administrator-defined and deterministic.
