# Splitser MCP

**Unofficial Python client and MCP server for [Splitser](https://splitser.com) / [WieBetaaltWat](https://wiebetaaltwat.nl).** Lists, expenses, members, balances, settlements via the web app API.

> [!NOTE]
> Not affiliated with Splitser BV or WieBetaaltWat. See [Disclaimer](#disclaimer).

> [!WARNING]
> This project was partially written by AI. Use at your own risk.

## About

Two packages in one repo:

| Path | Package | Purpose |
| --- | --- | --- |
| [`api/`](api/README.md) | `splitser-api` | Async HTTP client |
| [`mcp/`](mcp/README.md) | `splitser-mcp` | MCP tools for Cursor etc. |

Login is email/password. The client keeps a Rails session cookie on disk and hits the same JSON endpoints as `app.splitser.com` / `app.wiebetaaltwat.nl`. Splitser has no public API.

More for agents: [AGENTS.md](AGENTS.md).

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- A Splitser or WieBetaaltWat account

## MCP quick start

```bash
git clone https://github.com/jeroen-meijer/splitser-mcp.git
cd splitser-mcp/mcp
uv sync
export SPLITSER_EMAIL='you@example.com'
export SPLITSER_PASSWORD='your-password'
./run_mcp.sh
```

Cursor (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "splitser": {
      "command": "/path/to/splitser-mcp/mcp/run_mcp.sh",
      "env": {
        "SPLITSER_EMAIL": "you@example.com",
        "SPLITSER_PASSWORD": "your-password"
      }
    }
  }
}
```

WieBetaaltWat: `SPLITSER_BASE_URL=https://app.wiebetaaltwat.nl`, `SPLITSER_LANG=nl`.

## API only

```bash
cd api
uv sync
export SPLITSER_EMAIL='…'
export SPLITSER_PASSWORD='…'
uv run python -c "
import asyncio
from splitser_api import SplitserClient, SplitserConfig
async def main():
    async with SplitserClient(SplitserConfig.from_env()) as c:
        print((await c.current_user())['current_user']['email'])
asyncio.run(main())
"
```

Env vars and methods: [api/README.md](api/README.md).

## MCP tools

JSON in, JSON out. Full list: [mcp/README.md](mcp/README.md).

| Area | Examples |
| --- | --- |
| Session | `splitser_validate_session` |
| Lists | `splitser_list_lists`, `splitser_create_list` |
| Members | `splitser_add_member`, `splitser_friends_sync` |
| Expenses | `splitser_create_expense`, `splitser_update_expense`, `splitser_delete_expense` |
| Balances | `splitser_get_list_balance`, `splitser_list_balances` |
| Settlements | `splitser_settlement_preview`, `splitser_create_settle` |

Amounts are fractional cents (`1234` = EUR 12.34). MCP tools also take `amount_euros` where that helps.

## Out of scope

No iDEAL, Bancontact, payment requests, or bank linking. Use the official app for payments.

## Safety

Some tools write live data: expenses, members, settlements. Only use this on accounts and lists you own.

## Disclaimer

Unofficial. Not affiliated with or endorsed by Splitser BV, WieBetaaltWat, or related services.

The API is reverse-engineered from the web and mobile apps. Endpoints and auth can change without notice.

Mutating calls change real group expenses on your account. Provided as-is, no warranty. Your risk.
