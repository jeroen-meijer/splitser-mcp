"""Unofficial Splitser / WieBetaaltWat HTTP client."""

from .client import SplitserClient
from .config import SplitserConfig
from .errors import SplitserAuthError, SplitserError

__all__ = [
    "SplitserAuthError",
    "SplitserClient",
    "SplitserConfig",
    "SplitserError",
]
