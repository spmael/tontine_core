---
id: TASK-CLASSIC-004
status: shipped
started: 2026-10-18
completed: 2026-10-18
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

## Context

Randomization is an explicit, seeded construction step. Recipient selection
uses the resulting immutable order and never consumes randomness. The
randomization record travels with the rotation so persistence adapters can
retain its seed and provenance.

## Acceptance Criteria

- [x] Generate a rotation from a supplied active-member set and explicit seed.
- [x] Retain the seed, algorithm/version, input member set, generated order,
  actor, and timestamp in immutable provenance attached to the rotation, ready
  for persistence by an adapter.
- [x] Never randomize again during recipient lookup.
- [x] Reconstruct the same order from recorded randomization provenance.
- [x] Add tests for reproducibility and historical reconstruction.

## Planned Changes

- `src/tontine/classic/`
- `tests/classic/`

## Validation

```text
uv run pytest tests/classic
uv run ruff check src/tontine/classic tests/classic
uv run mypy src/tontine/classic/__init__.py
```

## Completion Notes

Randomization is explicit and seeded; recipient lookups use the stored immutable
order. The provenance is exposed on the rotation for persistence adapters; this
framework-independent core does not add durable storage.
