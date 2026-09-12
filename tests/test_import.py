"""Smoke tests for the public package boundary."""

import tontine


def test_public_package_imports() -> None:
    """Expose the package and its initial version."""
    assert tontine.__version__ == "0.1.0"
    assert tontine.TontineError.__name__ == "TontineError"
