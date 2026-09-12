"""Domain exceptions raised by tontine-core."""


class TontineError(Exception):
    """Base exception for expected tontine domain errors."""


class InvalidCurrencyError(TontineError):
    """Raised when a currency value is not a supported ISO code."""


class DuplicateMemberError(TontineError):
    """Raised when a member identifier is reused within a tontine."""


class DuplicateGroupError(TontineError):
    """Raised when a tontine identifier is reused within the repository."""


class DuplicateContributionError(TontineError):
    """Raised when a contribution is recorded more than once without adjustment."""


class UnsafeAccountReferenceError(TontineError):
    """Raised when an account reference may contain an unmasked secret."""


class DuplicateAccountError(TontineError):
    """Raised when a financial account identifier is registered more than once."""


class InvalidCountryError(TontineError):
    """Raised when a country code is not a known ISO 3166-1 alpha-2 code."""


class InvalidMembershipTransitionError(TontineError):
    """Raised when a membership status transition is not permitted."""
