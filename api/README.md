# splitser-api

Async Python client for the Splitser / WieBetaaltWat web API.

> [!NOTE]
> Not affiliated with Splitser BV or WieBetaaltWat. See [Disclaimer](../README.md#disclaimer).

> [!WARNING]
> This project was partially written by AI. Use at your own risk.

## Install

```bash
cd api
uv sync
```

Python 3.14+, [uv](https://docs.astral.sh/uv/).

## Auth

Email and password. Cookie `_wbw_rails_session` goes in a Mozilla-format jar on disk.

```bash
export SPLITSER_EMAIL='you@example.com'
export SPLITSER_PASSWORD='your-password'

# optional
export SPLITSER_BASE_URL='https://app.splitser.com'      # or https://app.wiebetaaltwat.nl
export SPLITSER_COOKIE_FILE='$HOME/.local/share/splitser-mcp/cookies.txt'
export SPLITSER_LANG='en'                                 # nl for WieBetaaltWat
```

First run signs in and writes the cookie file. Later runs reuse the session until it expires.

Do not commit credentials or cookie files.

## Usage

```python
import asyncio

from splitser_api import SplitserClient, SplitserConfig


async def main() -> None:
    config = SplitserConfig.from_env()
    async with SplitserClient(config) as client:
        me = await client.current_user()
        lists = await client.list_lists()
        print(me["current_user"]["email"], len(lists.get("data", [])))


asyncio.run(main())
```

### Create an expense

Equal split:

```python
await client.create_expense(
    list_id="…",
    name="Groceries",
    payed_by_member_id="…",
    payed_on="2026-08-31",
    amount_euros="12.34",
    split_member_ids=["…", "…"],
)
```

Fixed amounts plus share remainder (rest split by factor weights):

```python
await client.create_expense(
    list_id="…",
    name="Dinner",
    payed_by_member_id="…",
    payed_on="2026-08-31",
    amount_euros="12.34",
    shares=[
        {"member_id": "…", "exact_euros": "5.00"},
        {"member_id": "…", "exact_euros": "2.50"},
        {"member_id": "…", "factor": 2},
        {"member_id": "…", "factor": 1},
    ],
)
```

Each share row uses exactly one of `exact_euros`, `exact_fractional`, `factor`, or `percent`.
Exact rows are fixed; the leftover is split by `factor` weights or `percent` of the remainder.

## Amounts

Fractional cents: `1234` = EUR 12.34. Helpers: `splitser_api.money.euros_to_fractional`, `fractional_to_euros`.

## Client methods

| Area | Methods |
| --- | --- |
| Auth | `sign_in`, `sign_out`, `current_user` |
| Lists | `list_lists`, `get_list`, `create_list`, `update_list` |
| Members | `list_members`, `add_member_by_nickname`, `add_member_by_user_id`, `delete_member`, `create_list_invitation` |
| Expenses | `list_expenses`, `get_expense`, `create_expense`, `update_expense`, `delete_expense` |
| Balances | `get_list_balance`, `list_balances` |
| Settlements | `settlement_preview`, `list_settles`, `get_settle`, `create_settle` |
| Other | `friends_sync`, `search_categories` |

No iDEAL/Bancontact, payment requests, or bank linking.

## Tests

```bash
uv run pytest -q
uv run ruff check src tests
```

Live (optional):

```bash
SPLITSER_EMAIL=… SPLITSER_PASSWORD=… RUN_INTEGRATION_TESTS=1 uv run pytest -q -m integration
```

Repo root: [../README.md](../README.md). Agents: [../AGENTS.md](../AGENTS.md).
