"""Splitser web API client."""

from __future__ import annotations

import uuid
from typing import Any, Literal

import httpx

from .config import SplitserConfig
from .errors import SplitserAuthError, SplitserError
from .money import euros_to_fractional, money_dict
from .session import CookieStore

OTHER_CATEGORY = {"id": 999999999, "category_source": "auto"}


class SplitserClient:
    def __init__(
        self,
        config: SplitserConfig | None = None,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config or SplitserConfig.from_env()
        self._cookie_store = CookieStore(self.config.cookie_file)
        self._cookie_jar = self._cookie_store.load()
        self._client = http_client
        self._owns_client = http_client is None
        self._authenticated = False

    async def __aenter__(self) -> SplitserClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                cookies=self._cookie_jar,
                timeout=self.config.timeout_s,
                headers=self._default_headers(),
                trust_env=False,
            )
            self._seed_lang_cookie()
        await self.ensure_authenticated()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self._persist_cookies()
        if self._owns_client and self._client is not None:
            await self._client.aclose()

    def _default_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.config.user_agent,
            "Accept": "application/json",
            "Accept-Language": self.config.lang,
            "Accept-Version": self.config.accept_version,
            "X-App-React": "true",
            "Origin": self.config.base_url,
        }

    def _seed_lang_cookie(self) -> None:
        if self._client is None:
            return
        host = httpx.URL(self.config.base_url).host
        if host:
            self._client.cookies.set("_wbw_lang", self.config.lang, domain=host)

    def _require_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Client not initialized. Use `async with SplitserClient()`.")
        return self._client

    def _persist_cookies(self) -> None:
        jar = getattr(self._require_client().cookies, "jar", None)
        if jar is not None:
            self._cookie_store.save(jar)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        auth: bool = True,
    ) -> Any:
        if auth:
            await self.ensure_authenticated()

        client = self._require_client()
        url = f"{self.config.base_url}{path}"
        headers = {"Content-Type": "application/json"} if json is not None else None
        response = await client.request(method, url, json=json, params=params, headers=headers)

        if response.status_code in {401, 403} and auth:
            self._authenticated = False
            await self.sign_in()
            response = await client.request(method, url, json=json, params=params, headers=headers)

        if response.status_code in {401, 403}:
            raise SplitserAuthError(
                f"Authentication failed for {method} {path} ({response.status_code})"
            )
        if response.status_code >= 400:
            detail = response.text.strip()
            raise SplitserError(
                f"Splitser API error {response.status_code} for {method} {path}: {detail}"
            )

        self._persist_cookies()
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    async def ensure_authenticated(self) -> None:
        if self._authenticated:
            return

        client = self._require_client()
        response = await client.get(f"{self.config.base_url}/api/users/current")
        self._persist_cookies()
        if response.status_code == 200:
            payload = response.json()
            if payload.get("current_user"):
                self._authenticated = True
                return

        await self.sign_in()

    async def sign_in(self) -> dict[str, Any]:
        self.config.validate_credentials()
        client = self._require_client()
        response = await client.post(
            f"{self.config.base_url}/api/users/sign_in",
            json={"user": {"email": self.config.email, "password": self.config.password}},
            headers={"Content-Type": "application/json"},
        )
        self._persist_cookies()
        if response.status_code >= 400:
            raise SplitserAuthError(
                f"Sign in failed ({response.status_code}): {response.text.strip()}"
            )
        self._authenticated = True
        return response.json()

    async def sign_out(self) -> None:
        client = self._require_client()
        response = await client.delete(f"{self.config.base_url}/api/users/sign_out")
        self._persist_cookies()
        if response.status_code >= 400:
            raise SplitserError(
                f"Sign out failed ({response.status_code}): {response.text.strip()}"
            )
        self._authenticated = False

    async def current_user(self) -> dict[str, Any]:
        return await self._request("GET", "/api/users/current")

    async def list_lists(self) -> dict[str, Any]:
        return await self._request("GET", "/api/lists")

    async def get_list(self, list_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/lists/{list_id}")

    async def create_list(self, *, name: str, currency: str = "EUR") -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/lists",
            json={"list": {"name": name, "currency": currency}},
        )

    async def update_list(
        self,
        list_id: str,
        *,
        name: str,
        currency: str = "EUR",
    ) -> dict[str, Any]:
        return await self._request(
            "PATCH",
            f"/api/lists/{list_id}",
            json={"list": {"name": name, "currency": currency}},
        )

    async def list_members(self, list_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/lists/{list_id}/members")

    async def add_member_by_nickname(self, list_id: str, *, nickname: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/lists/{list_id}/members",
            json={"member": {"nickname": nickname}},
        )

    async def add_member_by_user_id(self, list_id: str, *, user_id: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/lists/{list_id}/members",
            json={"member": {"user_id": user_id}},
        )

    async def delete_member(self, member_id: str) -> dict[str, Any]:
        return await self._request("DELETE", f"/api/members/{member_id}")

    async def create_list_invitation(self, list_id: str) -> dict[str, Any]:
        return await self._request("POST", f"/api/lists/{list_id}/invitations", json={})

    async def list_expenses(
        self,
        list_id: str,
        *,
        page: int = 1,
        per_page: int = 15,
        settled: bool = False,
    ) -> dict[str, Any]:
        return await self._request(
            "GET",
            f"/api/lists/{list_id}/list_items",
            params={
                "page": page,
                "per_page": per_page,
                "sort[payed_on]": "desc",
                "sort[created_at]": "desc",
                "filter[settled]": str(settled).lower(),
            },
        )

    async def get_expense(self, expense_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/expenses/{expense_id}")

    async def create_expense(
        self,
        list_id: str,
        *,
        name: str,
        amount_fractional: int | None = None,
        amount_euros: str | float | None = None,
        payed_by_member_id: str,
        payed_on: str,
        member_shares: list[dict[str, Any]] | None = None,
        split_member_ids: list[str] | None = None,
        split_type: Literal["equal", "percent"] = "equal",
        percents: list[float] | None = None,
        expense_id: str | None = None,
        currency: str = "EUR",
    ) -> dict[str, Any]:
        fractional = amount_fractional
        if fractional is None:
            if amount_euros is None:
                raise ValueError("Provide amount_fractional or amount_euros")
            fractional = euros_to_fractional(amount_euros)

        shares_attributes = member_shares or self._build_shares_attributes(
            total_fractional=fractional,
            currency=currency,
            split_member_ids=split_member_ids or [payed_by_member_id],
            split_type=split_type,
            percents=percents,
        )

        payload = {
            "expense": {
                "id": expense_id or str(uuid.uuid4()),
                "category": OTHER_CATEGORY,
                "name": name,
                "payed_by_id": payed_by_member_id,
                "payed_on": payed_on,
                "source_amount": money_dict(fractional, currency),
                "amount": money_dict(fractional, currency),
                "exchange_rate": 1,
                "shares_attributes": shares_attributes,
            }
        }
        return await self._request(
            "POST",
            f"/api/lists/{list_id}/expenses",
            json=payload,
        )

    async def update_expense(
        self,
        expense_id: str,
        *,
        name: str,
        amount_fractional: int,
        payed_by_member_id: str,
        payed_on: str,
        shares: list[dict[str, Any]],
        currency: str = "EUR",
    ) -> dict[str, Any]:
        payload = {
            "expense": {
                "id": expense_id,
                "category": OTHER_CATEGORY,
                "name": name,
                "payed_by_id": payed_by_member_id,
                "payed_on": payed_on,
                "source_amount": money_dict(amount_fractional, currency),
                "amount": money_dict(amount_fractional, currency),
                "exchange_rate": 1,
                "shares": shares,
            }
        }
        return await self._request("PUT", f"/api/expenses/{expense_id}", json=payload)

    async def delete_expense(self, expense_id: str) -> dict[str, Any]:
        return await self._request("DELETE", f"/api/expenses/{expense_id}")

    async def get_list_balance(self, list_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/lists/{list_id}/balance")

    async def list_balances(self) -> dict[str, Any]:
        return await self._request("GET", "/api/balances")

    async def settlement_preview(self, list_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/lists/{list_id}/settlement_preview")

    async def list_settles(self, list_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/lists/{list_id}/settles")

    async def get_settle(self, settle_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/settles/{settle_id}")

    async def create_settle(self, list_id: str) -> dict[str, Any]:
        return await self._request("POST", f"/api/lists/{list_id}/settles")

    async def friends_sync(self, *, limit: int = 250) -> dict[str, Any]:
        return await self._request("GET", "/api/friends/sync", params={"limit": limit})

    async def search_categories(self, query: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/categories/search",
            json={"category_search": {"query": query}},
        )

    @staticmethod
    def _build_shares_attributes(
        *,
        total_fractional: int,
        currency: str,
        split_member_ids: list[str],
        split_type: Literal["equal", "percent"],
        percents: list[float] | None,
    ) -> list[dict[str, Any]]:
        if not split_member_ids:
            raise ValueError("split_member_ids must not be empty")

        if split_type == "percent":
            if not percents or len(percents) != len(split_member_ids):
                raise ValueError("percents must match split_member_ids for percent splits")
            shares: list[dict[str, Any]] = []
            allocated = 0
            for index, (member_id, percent) in enumerate(
                zip(split_member_ids, percents, strict=True)
            ):
                if index == len(split_member_ids) - 1:
                    share_amount = total_fractional - allocated
                else:
                    share_amount = round(total_fractional * percent)
                    allocated += share_amount
                shares.append(
                    {
                        "id": member_id,
                        "member_id": member_id,
                        "meta": {"type": "percent", "multiplier": percent},
                        "source_amount": money_dict(share_amount, currency),
                    }
                )
            return shares

        count = len(split_member_ids)
        base, remainder = divmod(total_fractional, count)
        shares = []
        for index, member_id in enumerate(split_member_ids):
            share_amount = base + (1 if index < remainder else 0)
            shares.append(
                {
                    "id": member_id,
                    "member_id": member_id,
                    "meta": {"type": "factor", "multiplier": 1},
                    "source_amount": money_dict(share_amount, currency),
                }
            )
        return shares
