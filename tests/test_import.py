"""Smoke tests for the public package boundary."""

import tontine
import tontine.exceptions as domain_exceptions


def test_public_package_imports() -> None:
    """Expose the package and its initial version."""
    assert tontine.__version__ == "0.1.0"
    assert tontine.TontineError.__name__ == "TontineError"
    assert tontine.MissingRecordError.__name__ == "MissingRecordError"
    assert issubclass(tontine.MissingRecordError, tontine.TontineError)
    assert not issubclass(tontine.MissingRecordError, KeyError)


def test_domain_exception_surface_is_framework_independent() -> None:
    """Keep every exported domain exception rooted in the core hierarchy."""
    assert tontine.TontineError.__bases__ == (Exception,)
    for name in domain_exceptions.__all__:
        error_type = getattr(domain_exceptions, name)
        assert error_type.__module__ == "tontine.exceptions"
        if error_type is not tontine.TontineError:
            assert error_type.__bases__ == (tontine.TontineError,)
