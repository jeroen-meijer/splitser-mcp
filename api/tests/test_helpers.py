from http.cookiejar import Cookie
from pathlib import Path

from splitser_api.config import default_cookie_file
from splitser_api.money import euros_to_fractional, fractional_to_euros
from splitser_api.session import CookieStore


def test_default_cookie_file_under_xdg() -> None:
    path = default_cookie_file()
    assert path.name == "cookies.txt"
    assert path.parent.name == "splitser-mcp"


def test_cookie_store_roundtrip(tmp_path: Path) -> None:
    store = CookieStore(tmp_path / "cookies.txt")
    jar = store.load()
    jar.set_cookie(
        Cookie(
            0,
            "_wbw_rails_session",
            "abc123",
            None,
            False,
            "app.splitser.com",
            False,
            False,
            "/",
            False,
            True,
            None,
            False,
            None,
            None,
            {},
        )
    )
    store.save(jar)

    reloaded = store.load()
    assert reloaded._cookies  # noqa: SLF001


def test_money_helpers() -> None:
    assert euros_to_fractional("12.34") == 1234
    assert euros_to_fractional(5.5) == 550
    assert fractional_to_euros(1234) == "12.34"
    assert fractional_to_euros(-99) == "-0.99"
