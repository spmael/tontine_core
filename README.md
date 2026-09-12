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
