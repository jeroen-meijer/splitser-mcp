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
        "Unofficial Splitser / WieBetaaltWat MCP. Write tools change real account data. "
        "Every tool returns pretty-printed JSON. "
        "IDs are UUIDs from list, member, and expense responses. "
        "Prefer amount_euros ('12.34'); amount_fractional is cents (1234 = EUR 12.34). "
        "payed_on is YYYY-MM-DD. "
        "For expenses, use list member ids from list_members (not always the user id). "
        "Settled expenses usually cannot be updated or deleted. "
        "Nickname invite: anonymous member + invite link; no email from nickname alone. "
        "No iDEAL, Bancontact, payment requests, or bank linking."
    ),
)

_config = SplitserConfig.from_env()


def _pretty_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def _parse_shares_arg(
    value: str | list[dict[str, Any]] | None,
) -> list[dict[str, Any]] | None:
    if value is None:
        return None
    if isinstance(value, str):
        parsed = json.loads(value)
        if not isinstance(parsed, list):
            raise ValueError("shares must be a JSON array")
        return parsed
    return value


async def _with_client(coro):
    async with SplitserClient(_config) as client:
        return await coro(client)


@mcp.tool()
async def splitser_validate_session() -> str:
    """Return the current user (email, id, preferences).

    Signs in with SPLITSER_EMAIL / SPLITSER_PASSWORD when the cookie jar has no
    valid session.
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.current_user())

    return await _with_client(_run)


@mcp.tool()
async def splitser_list_lists() -> str:
    """List the signed-in user's expense lists (id, name, currency, …).

    Take list ids from here for members, expenses, balances, and settles.
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.list_lists())

    return await _with_client(_run)


@mcp.tool()
async def splitser_get_list(list_id: str) -> str:
    """Get one list by UUID.

    Args:
        list_id: From splitser_list_lists or splitser_create_list.
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.get_list(list_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_create_list(name: str, currency: str = "EUR") -> str:
    """Create a list. You are added as the first member.

    Args:
        name: List title.
        currency: ISO code (default EUR).
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.create_list(name=name, currency=currency))

    return await _with_client(_run)


@mcp.tool()
async def splitser_update_list(list_id: str, name: str, currency: str = "EUR") -> str:
    """Rename a list or change its currency.

    Args:
        list_id: List UUID.
        name: New title (API always wants a name, even if you only change currency).
        currency: ISO code (default EUR).
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.update_list(list_id, name=name, currency=currency))

    return await _with_client(_run)


@mcp.tool()
async def splitser_list_members(list_id: str) -> str:
    """List members on a list (id, nickname, invite/anonymous state).

    Use these member ids as payed_by_member_id and in expense shares. They are
    list member UUIDs and may differ from Splitser user ids.

    Args:
        list_id: List UUID.
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.list_members(list_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_add_member(
    list_id: str,
    nickname: str | None = None,
    user_id: str | None = None,
) -> str:
    """Add one member. Pass nickname or user_id, not both.

    nickname: anonymous placeholder. Get a link with splitser_create_list_invitation
    (no invite email from nickname alone).
    user_id: existing Splitser user (often from splitser_friends_sync).

    Args:
        list_id: List UUID.
        nickname: Display name for a new placeholder.
        user_id: Existing Splitser user UUID.
    """

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
    """Remove a member from a list.

    Args:
        member_id: Member UUID from splitser_list_members (not the list id).
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.delete_member(member_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_create_list_invitation(list_id: str) -> str:
    """Create an invite link for a list (URL in the JSON). Does not send email.

    Args:
        list_id: List UUID.
    """

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
    """Page through expenses on a list.

    Args:
        list_id: List UUID.
        page: 1-based page.
        per_page: Page size (default 15).
        settled: False = open expenses (default). True = already settled.
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(
            await client.list_expenses(list_id, page=page, per_page=per_page, settled=settled)
        )

    return await _with_client(_run)


@mcp.tool()
async def splitser_get_expense(expense_id: str) -> str:
    """Get one expense (amount, payer, shares, settle_id, category).

    Args:
        expense_id: From splitser_list_expenses or splitser_create_expense.
    """

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
    shares: str | list[dict[str, Any]] | None = None,
    split_member_ids: list[str] | None = None,
    split_type: Literal["equal", "percent"] = "equal",
    percents: list[float] | None = None,
    currency: str = "EUR",
) -> str:
    """Create an expense. Pass amount_euros or amount_fractional.

    Split with either shares (custom / hybrid) or split_member_ids.
    shares: use when some people take a fixed amount and others split the rest.
    split_member_ids: equal split by default, or split_type=percent with percents
    as fractions 0..1 aligned to the member list (e.g. [0.5, 0.5]). If both shares
    and split_member_ids are omitted, only the payer is charged.

    Each share row needs member_id and exactly one of exact_euros ('5.00'),
    exact_fractional (500), factor (weight, e.g. 2), or percent (fraction of the
    remainder after exacts, e.g. 0.5). Exact rows are fixed. The leftover is split
    by factor or by percent. Do not mix factor and percent. Example:
    [{"member_id":"<id>","exact_euros":"5.00"},{"member_id":"<id>","exact_euros":"2.50"},
    {"member_id":"<id>","factor":2},{"member_id":"<id>","factor":1}].
    Rows that already have a meta object are sent through as-is.

    Args:
        list_id: List UUID.
        name: Expense description.
        payed_by_member_id: Member UUID who paid (from list_members).
        payed_on: YYYY-MM-DD.
        amount_euros: Euros as string or number, e.g. '12.34'.
        amount_fractional: Cents, e.g. 1234 for EUR 12.34.
        shares: Share rows (list or JSON string).
        split_member_ids: Members for a simple equal/percent split.
        split_type: equal or percent (ignored when shares is set).
        percents: Fractions for percent; same length as split_member_ids.
        currency: ISO code (default EUR).
    """

    async def _run(client: SplitserClient) -> str:
        resolved_shares = _parse_shares_arg(shares)
        return _pretty_json(
            await client.create_expense(
                list_id,
                name=name,
                amount_euros=amount_euros,
                amount_fractional=amount_fractional,
                payed_by_member_id=payed_by_member_id,
                payed_on=payed_on,
                shares=resolved_shares,
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
    """Update an unsettled expense. shares_json is required (full share list).

    Settled expenses usually fail to update. Pass amount_euros or amount_fractional.
    Replace the whole split with shares_json (same row shape as create, or raw
    Splitser rows with meta).

    Each share row needs member_id and exactly one of exact_euros ('5.00'),
    exact_fractional (500), factor (weight, e.g. 2), or percent (fraction of the
    remainder after exacts, e.g. 0.5). Exact rows are fixed. The leftover is split
    by factor or by percent. Do not mix factor and percent. Example:
    [{"member_id":"<id>","exact_euros":"5.00"},{"member_id":"<id>","exact_euros":"2.50"},
    {"member_id":"<id>","factor":2},{"member_id":"<id>","factor":1}].

    Args:
        expense_id: Expense UUID.
        name: Description.
        payed_by_member_id: Member UUID who paid.
        payed_on: YYYY-MM-DD.
        amount_euros: Euros as string or number.
        amount_fractional: Cents.
        shares_json: Share rows (list or JSON string).
        currency: ISO code (default EUR).
    """

    async def _run(client: SplitserClient) -> str:
        fractional = amount_fractional
        if fractional is None:
            if amount_euros is None:
                raise ValueError("Provide amount_euros or amount_fractional")
            fractional = euros_to_fractional(amount_euros)
        resolved = _parse_shares_arg(shares_json)
        if resolved is None:
            raise ValueError("shares_json is required for updates")
        return _pretty_json(
            await client.update_expense(
                expense_id,
                name=name,
                amount_fractional=fractional,
                payed_by_member_id=payed_by_member_id,
                payed_on=payed_on,
                shares=resolved,
                currency=currency,
            )
        )

    return await _with_client(_run)


@mcp.tool()
async def splitser_delete_expense(expense_id: str) -> str:
    """Delete an unsettled expense.

    Settled expenses usually cannot be deleted.

    Args:
        expense_id: Expense UUID.
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.delete_expense(expense_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_get_list_balance(list_id: str) -> str:
    """Balance per member on one list (who owes / is owed).

    Args:
        list_id: List UUID.
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.get_list_balance(list_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_list_balances() -> str:
    """Your balances on every list."""

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.list_balances())

    return await _with_client(_run)


@mcp.tool()
async def splitser_settlement_preview(list_id: str) -> str:
    """Show who should pay whom before settling. Does not create a settlement.

    Uses unsettled expenses. Empty commitments usually means nothing left to settle.

    Args:
        list_id: List UUID.
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.settlement_preview(list_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_list_settles(list_id: str) -> str:
    """List past settlements on a list.

    Args:
        list_id: List UUID.
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.list_settles(list_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_get_settle(settle_id: str) -> str:
    """Get one settlement (commitments, linked expenses).

    Args:
        settle_id: From splitser_list_settles or splitser_create_settle.
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.get_settle(settle_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_create_settle(list_id: str) -> str:
    """Settle a list: lock current unsettled expenses into a settlement.

    Write call. Those expenses then usually cannot be edited or deleted.
    Call splitser_settlement_preview first if you want to check the plan.

    Args:
        list_id: List UUID.
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.create_settle(list_id))

    return await _with_client(_run)


@mcp.tool()
async def splitser_friends_sync(limit: int = 250) -> str:
    """List Splitser friends you can add with splitser_add_member(user_id=…).

    Args:
        limit: Max friends (default 250).
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.friends_sync(limit=limit))

    return await _with_client(_run)


@mcp.tool()
async def splitser_search_categories(query: str) -> str:
    """Suggest a category for an expense description.

    create/update still use a default category; this is for lookup only.

    Args:
        query: Free text, e.g. groceries or taxi.
    """

    async def _run(client: SplitserClient) -> str:
        return _pretty_json(await client.search_categories(query))

    return await _with_client(_run)


def main() -> None:
    if not os.environ.get("SPLITSER_EMAIL") or not os.environ.get("SPLITSER_PASSWORD"):
        raise SystemExit("SPLITSER_EMAIL and SPLITSER_PASSWORD must be set")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
