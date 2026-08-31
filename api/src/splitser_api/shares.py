"""Build Splitser expense share attributes from high-level specs.

Each member uses one of exact / factor / percent:

```python
{"member_id": "...", "exact_euros": "5.00"}
{"member_id": "...", "exact_fractional": 250}
{"member_id": "...", "factor": 2}
{"member_id": "...", "percent": 0.5}  # of remainder after exacts (or of total if none)
```

Upstream meta: ``exact`` (fixed), ``factor`` (weight), ``percent``.
"""

from __future__ import annotations

from typing import Any, Literal

from .money import euros_to_fractional, money_dict

ShareKind = Literal["exact", "factor", "percent"]


def is_raw_shares(shares: list[dict[str, Any]]) -> bool:
    """True when items already look like Splitser shares_attributes / shares."""
    return bool(shares) and all("meta" in item for item in shares)


def build_shares_attributes(
    *,
    total_fractional: int,
    currency: str,
    shares: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Turn high-level share specs into Splitser ``shares_attributes`` rows."""
    if not shares:
        raise ValueError("shares must not be empty")
    if is_raw_shares(shares):
        return shares

    parsed = [_parse_spec(item) for item in shares]
    member_ids = [p["member_id"] for p in parsed]
    if len(set(member_ids)) != len(member_ids):
        raise ValueError("duplicate member_id in shares")

    exacts = [p for p in parsed if p["kind"] == "exact"]
    factors = [p for p in parsed if p["kind"] == "factor"]
    percents = [p for p in parsed if p["kind"] == "percent"]

    if factors and percents:
        raise ValueError("cannot mix factor and percent shares in one expense")

    exact_total = sum(int(p["value"]) for p in exacts)
    if exact_total > total_fractional:
        raise ValueError(
            f"exact shares ({exact_total}) exceed expense total ({total_fractional})"
        )

    remainder = total_fractional - exact_total
    if not factors and not percents:
        if exact_total != total_fractional:
            raise ValueError(
                f"exact-only shares must sum to total ({exact_total} != {total_fractional})"
            )
        return [_exact_row(p["member_id"], int(p["value"]), currency) for p in exacts]

    if remainder < 0:
        raise ValueError("remainder after exact shares is negative")

    out: list[dict[str, Any]] = [
        _exact_row(p["member_id"], int(p["value"]), currency) for p in exacts
    ]

    if factors:
        out.extend(
            _weighted_factor_rows(
                members=[(p["member_id"], float(p["value"])) for p in factors],
                remainder=remainder,
                currency=currency,
            )
        )
        return out

    out.extend(
        _percent_rows(
            members=[(p["member_id"], float(p["value"])) for p in percents],
            remainder=remainder,
            currency=currency,
        )
    )
    return out


def build_equal_shares(
    *,
    total_fractional: int,
    currency: str,
    member_ids: list[str],
) -> list[dict[str, Any]]:
    if not member_ids:
        raise ValueError("member_ids must not be empty")
    return build_shares_attributes(
        total_fractional=total_fractional,
        currency=currency,
        shares=[{"member_id": mid, "factor": 1} for mid in member_ids],
    )


def build_percent_shares(
    *,
    total_fractional: int,
    currency: str,
    member_ids: list[str],
    percents: list[float],
) -> list[dict[str, Any]]:
    if len(member_ids) != len(percents):
        raise ValueError("percents must match member_ids")
    return build_shares_attributes(
        total_fractional=total_fractional,
        currency=currency,
        shares=[
            {"member_id": mid, "percent": pct}
            for mid, pct in zip(member_ids, percents, strict=True)
        ],
    )


def _parse_spec(item: dict[str, Any]) -> dict[str, Any]:
    member_id = item.get("member_id")
    if not member_id or not isinstance(member_id, str):
        raise ValueError("each share needs member_id")

    keys = [
        k
        for k in ("exact_euros", "exact_fractional", "factor", "percent")
        if k in item and item[k] is not None
    ]
    if len(keys) != 1:
        raise ValueError(
            "each share needs exactly one of exact_euros, exact_fractional, factor, percent"
        )
    key = keys[0]
    if key == "exact_euros":
        return {
            "member_id": member_id,
            "kind": "exact",
            "value": euros_to_fractional(item["exact_euros"]),
        }
    if key == "exact_fractional":
        return {"member_id": member_id, "kind": "exact", "value": int(item["exact_fractional"])}
    if key == "factor":
        factor = float(item["factor"])
        if factor <= 0:
            raise ValueError("factor must be > 0")
        return {"member_id": member_id, "kind": "factor", "value": factor}
    percent = float(item["percent"])
    if percent < 0:
        raise ValueError("percent must be >= 0")
    return {"member_id": member_id, "kind": "percent", "value": percent}


def _exact_row(member_id: str, fractional: int, currency: str) -> dict[str, Any]:
    return {
        "id": member_id,
        "member_id": member_id,
        "meta": {"type": "exact", "multiplier": 0},
        "source_amount": money_dict(fractional, currency),
    }


def _factor_row(
    member_id: str, multiplier: float, fractional: int, currency: str
) -> dict[str, Any]:
    return {
        "id": member_id,
        "member_id": member_id,
        "meta": {"type": "factor", "multiplier": multiplier},
        "source_amount": money_dict(fractional, currency),
    }


def _percent_row(
    member_id: str, multiplier: float, fractional: int, currency: str
) -> dict[str, Any]:
    return {
        "id": member_id,
        "member_id": member_id,
        "meta": {"type": "percent", "multiplier": multiplier},
        "source_amount": money_dict(fractional, currency),
    }


def _weighted_factor_rows(
    *,
    members: list[tuple[str, float]],
    remainder: int,
    currency: str,
) -> list[dict[str, Any]]:
    if not members:
        raise ValueError("need at least one factor share for the remainder")
    if remainder == 0:
        return [
            _factor_row(member_id, multiplier, 0, currency)
            for member_id, multiplier in members
        ]

    weight_sum = sum(multiplier for _, multiplier in members)
    rows: list[dict[str, Any]] = []
    allocated = 0
    for index, (member_id, multiplier) in enumerate(members):
        if index == len(members) - 1:
            amount = remainder - allocated
        else:
            amount = round(remainder * multiplier / weight_sum)
            allocated += amount
        rows.append(_factor_row(member_id, multiplier, amount, currency))
    return rows


def _percent_rows(
    *,
    members: list[tuple[str, float]],
    remainder: int,
    currency: str,
) -> list[dict[str, Any]]:
    if not members:
        raise ValueError("need at least one percent share for the remainder")
    rows: list[dict[str, Any]] = []
    allocated = 0
    for index, (member_id, percent) in enumerate(members):
        if index == len(members) - 1:
            amount = remainder - allocated
        else:
            amount = round(remainder * percent)
            allocated += amount
        rows.append(_percent_row(member_id, percent, amount, currency))
    return rows
