# tontine-core

Build a simple, transparent, auditable, and reusable Python engine for community
tontines.

## Package Identity

- Distribution name: `tontine-core`
- Python import name: `tontine`
- Supported Python: 3.12+

## Development

This repository uses [uv](https://docs.astral.sh/uv/) to create the isolated
environment, resolve dependencies, run tools, and build the package.

```bash
uv sync
uv run pytest
uv run pytest --cov=tontine --cov-report=html --cov-report=term
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv build
```

Import the package with:

```python
import tontine
```

The core package is framework-independent and has no runtime dependency on a
database, web framework, payment provider, or financial institution.

## Publishing

Releases are published to PyPI by
[`.github/workflows/python-publish.yml`](.github/workflows/python-publish.yml)
when a GitHub Release is published. Before creating a release:

1. Update `project.version` in `pyproject.toml`.
2. Run the test, lint, type-check, and build commands above.
3. Create a GitHub Release whose tag matches the package version, such as
	`v0.1.0` for version `0.1.0`.

The workflow verifies the tag and package version, runs the tests, builds the
wheel and source distribution, and publishes both artifacts. PyPI Trusted
Publishing must be configured for:

- Repository: `spmael/tontine_core`
- Workflow: `python-publish.yml`
- GitHub environment: `pypi`

No PyPI API token is stored in the repository; publishing uses GitHub's OIDC
identity through the configured Trusted Publisher.

## Structured Reporting

Reporting APIs expose structured member and group statement data, including
contribution history, outstanding amounts, payouts, investment units, ownership,
cash, investments, liabilities, NAV, and proposals. For example, a consumer can
use a `MemberStatement` as the source for a web view or export. PDF, Excel, HTML,
and web rendering remain application-layer responsibilities.

## Financial Account Registry

The account registry records external custody context only. For example, a bank
account may be represented with `****1234`, `NG`, and a logical ledger identifier
such as `ledger-cash-ngn`. The package does not store credentials, connect to
institutions, retrieve live balances, initiate payments, or move real money.
