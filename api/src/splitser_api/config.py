"""Client config from env vars."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
)

SPLITSER_BASE_URL = "https://app.splitser.com"
WBW_BASE_URL = "https://app.wiebetaaltwat.nl"


def default_cookie_file() -> Path:
    xdg_data = os.environ.get("XDG_DATA_HOME")
    root = Path(xdg_data) if xdg_data else Path.home() / ".local" / "share"
    return root / "splitser-mcp" / "cookies.txt"


@dataclass(frozen=True)
class SplitserConfig:
    base_url: str = SPLITSER_BASE_URL
    email: str = ""
    password: str = ""
    cookie_file: Path = field(default_factory=default_cookie_file)
    lang: str = "en"
    timeout_s: float = 30.0
    user_agent: str = DEFAULT_USER_AGENT

    @classmethod
    def from_env(cls) -> SplitserConfig:
        base_url = os.environ.get("SPLITSER_BASE_URL", SPLITSER_BASE_URL).rstrip("/")
        cookie_file = os.environ.get("SPLITSER_COOKIE_FILE")
        return cls(
            base_url=base_url,
            email=os.environ.get("SPLITSER_EMAIL", ""),
            password=os.environ.get("SPLITSER_PASSWORD", ""),
            cookie_file=Path(cookie_file) if cookie_file else default_cookie_file(),
            lang=os.environ.get("SPLITSER_LANG", "en"),
            timeout_s=float(os.environ.get("SPLITSER_TIMEOUT_SECONDS", "30")),
            user_agent=os.environ.get("SPLITSER_USER_AGENT", DEFAULT_USER_AGENT),
        )

    def validate_credentials(self) -> None:
        if not self.email.strip() or not self.password:
            raise ValueError("SPLITSER_EMAIL and SPLITSER_PASSWORD are required")
