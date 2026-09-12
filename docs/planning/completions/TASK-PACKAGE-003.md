---
task: TASK-PACKAGE-003
status: shipped
started: 2026-09-12
completed: 2026-09-12
---

# Completion: TASK-PACKAGE-003

## Outcome

Added an import smoke test and documented installation, import, test, quality,
and build commands using uv.

## Acceptance Criteria Evidence

- [x] Package imports from `src/`: `uv run python -c "import tontine"`.
- [x] Isolated pytest smoke test passes: `tests/test_import.py` passed.
- [x] Source distribution and wheel build locally: `uv build` passed.
- [x] README shows installation and import commands: `README.md` package development section.

## Validation

```text
uv run pytest tests/test_import.py
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv build
```

All checks passed.

## Files Changed

- `tests/test_import.py`
- `README.md`

## Gaps and Follow-up

- Domain behavior tests will be added with the group and contribution capabilities.
