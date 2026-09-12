---
id: CAP-PACKAGE-001
status: ready
requirements:
  - FR-PKG-001
  - NFR-PKG-001
owner: package-foundation
---

# Capability: Package Foundation

## Outcome

Developers can install the `tontine-core` distribution and import the `tontine`
Python package from a standard `src/` layout with a repeatable local test and
quality-check workflow.

## Domain Boundary

- Inputs: package metadata, Python version, source files, test configuration
- Outputs: importable `tontine` package and installable `tontine-core` distribution
- Invariants: import name and distribution name remain distinct and stable
- Exclusions: domain behavior, persistence, web frameworks, and database setup

## Acceptance Criteria

- [ ] `src/tontine/__init__.py` exists and imports successfully.
- [ ] Distribution metadata names the project `tontine-core`.
- [ ] The supported Python baseline is Python 3.12 or newer.
- [ ] An isolated test command runs without a database or web framework.
- [ ] Quality tooling is configured without coupling the core package to a framework.
- [ ] README documentation explains installation and the import name.

## Implementation Tasks

- TASK-PACKAGE-001: Create the `src/tontine` package layout.
- TASK-PACKAGE-002: Configure package metadata and development tooling.
- TASK-PACKAGE-003: Add import, build, and test smoke checks.

## Verification

- Build: `python -m build`
- Tests: `python -m pytest`
- Import: `python -c "import tontine"`
