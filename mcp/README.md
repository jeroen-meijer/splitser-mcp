# splitser-mcp

MCP server on top of [`splitser-api`](../api/README.md). Uses `MCPServer` from the official Python MCP SDK (v2).

> [!NOTE]
> Not affiliated with Splitser BV or WieBetaaltWat. See [Disclaimer](../README.md#disclaimer).

> [!WARNING]
> This project was partially written by AI. Use at your own risk.

## Run

```bash
cd mcp
uv sync
export SPLITSER_EMAIL='you@example.com'
export SPLITSER_PASSWORD='your-password'
./run_mcp.sh
```

Stdio. Set credentials in env (or in your MCP client config).

## Cursor

`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "splitser": {
      "command": "/absolute/path/to/splitser-mcp/mcp/run_mcp.sh",
      "env": {
        "SPLITSER_EMAIL": "you@example.com",
        "SPLITSER_PASSWORD": "your-password"
      }
    }
  }
}
```

WieBetaaltWat: `"SPLITSER_BASE_URL": "https://app.wiebetaaltwat.nl"`, `"SPLITSER_LANG": "nl"`.

Reload MCP after edits.

## Tools

All return JSON strings.

### Session

| Tool | Purpose |
| --- | --- |
| `splitser_validate_session` | Logged-in user |

### Lists

| Tool | Purpose |
| --- | --- |
| `splitser_list_lists` | Your lists |
| `splitser_get_list` | One list |
| `splitser_create_list` | New list |
| `splitser_update_list` | Rename / change currency |

### Members

| Tool | Purpose |
| --- | --- |
| `splitser_list_members` | Members on a list |
| `splitser_add_member` | `nickname` (new) or `user_id` (existing) |
| `splitser_delete_member` | Remove member |
| `splitser_create_list_invitation` | Invite link |
| `splitser_friends_sync` | Friends you can add |

### Expenses

| Tool | Purpose |
| --- | --- |
| `splitser_list_expenses` | List expenses |
| `splitser_get_expense` | One expense |
| `splitser_create_expense` | Create (`amount_euros` or `amount_fractional`) |
| `splitser_update_expense` | Update (needs `shares_json`) |
| `splitser_delete_expense` | Delete |
| `splitser_search_categories` | Category by text |

### Balances and settlements

| Tool | Purpose |
| --- | --- |
| `splitser_get_list_balance` | Balance per member on one list |
| `splitser_list_balances` | Your balances on all lists |
| `splitser_settlement_preview` | Preview before settling |
| `splitser_list_settles` | Past settlements |
| `splitser_get_settle` | One settlement |
| `splitser_create_settle` | Settle a list |

Amounts: fractional cents (`1234` = EUR 12.34). On create/update you can pass `amount_euros` instead.

## Out of scope

No iDEAL/Bancontact or bank linking.

## Dev

```bash
uv run ruff check src
```

Repo root: [../README.md](../README.md). Agents: [../AGENTS.md](../AGENTS.md).
