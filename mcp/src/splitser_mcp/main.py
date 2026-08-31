"""MCP tools for Splitser / WieBetaaltWat."""

from __future__ import annotations

import json
import os
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer
from splitser_api.client import SplitserClient
from splitser_api.config import SplitserConfig
from splitser_api.money import euros_to_fractional

mcp = MCPServer(
    "Splitser",
    instructions=(
        "Splitser / WieBetaaltWat: lists, expenses, members, balances, settlements. "
        "Amounts are fractional cents (1234 = EUR 12.34) unless amount_euros is set. "
        "No iDEAL/Bancontact."
    ),
)

_config = SplitserConfig.from_env()


def _pretty_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


async def _with_client(coro):
    async with SplitserClient(_config) as client:
        return await coro(client)


@mcp.tool()
async def splitser_validate_session() -> str:
    """Return the logged-in user."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.current_user())

    return await _with_client(_run)


@mcp.tool()
async def splitser_list_lists() -> str:
    """List your expense lists."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.list_lists())

    return await _with_client(_run)


@mcp.tool()
async def splitser_get_list(list_id: str) -> str:
    """Fetch one list by id."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.get_list(list_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_create_list(name: str, currency: str = "EUR") -> str:
    """Create a list."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.create_list(name=name, currency=currency))

    return await _with_client(_run)


@mcp.tool()
async def splitser_update_list(list_id: str, name: str, currency: str = "EUR") -> str:
    """Rename a list or change its currency."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.update_list(list_id, name=name, currency=currency))

    return await _with_client(_run)


@mcp.tool()
async def splitser_list_members(list_id: str) -> str:
    """List members on a list."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.list_members(list_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_add_member(
    list_id: str,
    nickname: str | None = None,
    user_id: str | None = None,
) -> str:
    """Add a member. Pass nickname for a new person, or user_id for an existing Splitser user."""

    def _validate() -> str:
        if bool(nickname) == bool(user_id):
            return _pretty_json({"error": "Provide exactly one of nickname or user_id"})
        return ""

    preflight = _validate()
    if preflight:
        return preflight

    async def _run(client: SplitserClient) -> str:
        if nickname:
            payload = await client.add_member_by_nickname(list_id, nickname=nickname)
        else:
            payload = await client.add_member_by_user_id(list_id, user_id=user_id or "")
        return _pretty_json(payload)

    return await _with_client(_run)


@mcp.tool()
async def splitser_delete_member(member_id: str) -> str:
    """Remove a member from a list."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.delete_member(member_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_create_list_invitation(list_id: str) -> str:
    """Create an invitation link for a list."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.create_list_invitation(list_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_list_expenses(
    list_id: str,
    page: int = 1,
    per_page: int = 15,
    settled: bool = False,
) -> str:
    """List expenses on a list."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(
            await client.list_expenses(list_id, page=page, per_page=per_page, settled=settled)
        )

    return await _with_client(_run)


@mcp.tool()
async def splitser_get_expense(expense_id: str) -> str:
    """Get one expense by id."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.get_expense(expense_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_create_expense(
    list_id: str,
    name: str,
    payed_by_member_id: str,
    payed_on: str,
    amount_euros: str | float | None = None,
    amount_fractional: int | None = None,
    split_member_ids: list[str] | None = None,
    split_type: Literal["equal", "percent"] = "equal",
    percents: list[float] | None = None,
    currency: str = "EUR",
) -> str:
    """Add an expense. amount_euros (12.34) or amount_fractional (1234)."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(
            await client.create_expense(
                list_id,
                name=name,
                amount_euros=amount_euros,
                amount_fractional=amount_fractional,
                payed_by_member_id=payed_by_member_id,
                payed_on=payed_on,
                split_member_ids=split_member_ids,
                split_type=split_type,
                percents=percents,
                currency=currency,
            )
        )

    return await _with_client(_run)


@mcp.tool()
async def splitser_update_expense(
    expense_id: str,
    name: str,
    payed_by_member_id: str,
    payed_on: str,
    amount_euros: str | float | None = None,
    amount_fractional: int | None = None,
    shares_json: str | list[dict[str, Any]] | None = None,
    currency: str = "EUR",
) -> str:
    """Update an expense. shares_json is a JSON array (string or list) of share objects."""

    async def _run(client: SplitserClient) -> str:
        fractional = amount_fractional
        if fractional is None:
            if amount_euros is None:
                raise ValueError("Provide amount_euros or amount_fractional")
            fractional = euros_to_fractional(amount_euros)
        if shares_json is None:
            raise ValueError("shares_json is required for updates")
        if isinstance(shares_json, str):
            shares = json.loads(shares_json)
        else:
            shares = shares_json
        return _pretty_json(
            await client.update_expense(
                expense_id,
                name=name,
                amount_fractional=fractional,
                payed_by_member_id=payed_by_member_id,
                payed_on=payed_on,
                shares=shares,
                currency=currency,
            )
        )

    return await _with_client(_run)


@mcp.tool()
async def splitser_delete_expense(expense_id: str) -> str:
    """Delete an expense."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.delete_expense(expense_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_get_list_balance(list_id: str) -> str:
    """Per-member balances on one list."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.get_list_balance(list_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_list_balances() -> str:
    """Your balance on every list."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.list_balances())

    return await _with_client(_run)


@mcp.tool()
async def splitser_settlement_preview(list_id: str) -> str:
    """Preview settlement payments before you settle."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.settlement_preview(list_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_list_settles(list_id: str) -> str:
    """List settlements for a list."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.list_settles(list_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_get_settle(settle_id: str) -> str:
    """Get settlement details."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.get_settle(settle_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_create_settle(list_id: str) -> str:
    """Create a settlement for a list."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.create_settle(list_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_friends_sync(limit: int = 250) -> str:
    """List Splitser friends you can add to a list."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.friends_sync(limit=limit))

    return await _with_client(_run)


@mcp.tool()
async def splitser_search_categories(query: str) -> str:
    """Match an expense description to a category."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.search_categories(query))

    return await _with_client(_run)


def main() -> None:
    if not os.environ.get("SPLITSER_EMAIL") or not os.environ.get("SPLITSER_PASSWORD"):
        raise SystemExit("SPLITSER_EMAIL and SPLITSER_PASSWORD must be set")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
