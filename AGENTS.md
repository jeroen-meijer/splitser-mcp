# AGENTS.md

Notes for humans and coding agents.

## What this is

Unofficial Splitser / WieBetaaltWat client + MCP. Reverse-engineered web API, not official.

| Path | Package |
| --- | --- |
| `api/` | `splitser-api` |
| `mcp/` | `splitser-mcp` |

MCP: `mcp/run_mcp.sh` → `uv run python -m splitser_mcp` (stdio).

## Stack

- Python 3.14+, `uv`
- `httpx` in `splitser-api`
- MCP SDK 2.x: `MCPServer` from `mcp.server.mcpserver` (FastMCP is v1 / removed in v2)
- Auth: email/password → `_wbw_rails_session` in `~/.local/share/splitser-mcp/cookies.txt` (`SPLITSER_COOKIE_FILE` to override)

## Key paths

| Path | Purpose |
| --- | --- |
| `api/src/splitser_api/client.py` | HTTP client |
| `api/src/splitser_api/config.py` | Env config |
| `api/src/splitser_api/session.py` | Cookie jar |
| `api/src/splitser_api/money.py` | EUR ↔ fractional cents |
| `mcp/src/splitser_mcp/main.py` | Tools + `main()` |
| `mcp/run_mcp.sh` | Cursor entry |

## Commands

```bash
cd api && uv sync && uv run pytest -q && uv run ruff check src tests
cd mcp && uv sync && uv run ruff check src && ./run_mcp.sh
```

Live test:

```bash
cd api
SPLITSER_EMAIL=… SPLITSER_PASSWORD=… RUN_INTEGRATION_TESTS=1 uv run pytest -q -m integration
```

## Auth

- `SPLITSER_EMAIL`, `SPLITSER_PASSWORD` from env only. No secrets in git.
- Client: load cookies → `GET /api/users/current` → sign in if needed → save jar after requests.
- WieBetaaltWat: `SPLITSER_BASE_URL=https://app.wiebetaaltwat.nl`, `SPLITSER_LANG=nl`.

## API quirks

- Amounts: fractional cents (`1234` = EUR 12.34).
- Create expense: client UUID, POST uses `shares_attributes`.
- Update expense: PUT uses `shares` (not `shares_attributes`).
- Listing expenses: `GET …/list_items`.

## Rules

- No iDEAL/Bancontact, payment requests, bank linking unless asked.
- Mutating tools hit real Splitser data. Don't run them casually on the user's account.
- MCP tools return JSON strings.
- Extend `SplitserClient` first, thin wrappers in `main.py`.
- API can break when Splitser ships app updates.

## Git

Conventional commits: `feat(api): …`, `fix(mcp): …`. No AI-tool credit in commits or PRs.

## Docs

Plain and dry. No em dashes.
