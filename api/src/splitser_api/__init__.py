"""Unofficial Splitser / WieBetaaltWat HTTP client."""

from .client import SplitserClient
from .config import SplitserConfig
from .errors import SplitserAuthError, SplitserError
from .shares import build_shares_attributes

__all__ = [
    "SplitserAuthError",
    "SplitserClient",
    "SplitserConfig",
    "SplitserError",
    "build_shares_attributes",
]
