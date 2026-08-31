"""Client errors."""


class SplitserError(RuntimeError):
    """Base Splitser client error."""


class SplitserAuthError(SplitserError):
    """Authentication or session error."""
