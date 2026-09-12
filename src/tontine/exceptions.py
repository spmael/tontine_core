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


class InvalidMembershipTransitionError(TontineError):
    """Raised when a membership status transition is not permitted."""
