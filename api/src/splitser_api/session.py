"""Session cookie file I/O."""

from __future__ import annotations

import contextlib
from http.cookiejar import MozillaCookieJar
from pathlib import Path


class CookieStore:
    """Read and write a Mozilla-format cookie jar."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> MozillaCookieJar:
        jar = MozillaCookieJar(str(self.path))
        with contextlib.suppress(FileNotFoundError):
            jar.load(ignore_discard=True, ignore_expires=True)
        return jar

    def save(self, jar: MozillaCookieJar) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        jar.save(ignore_discard=True, ignore_expires=True)
