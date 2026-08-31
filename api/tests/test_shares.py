import pytest

from splitser_api.shares import build_equal_shares, build_shares_attributes


def test_hybrid_exact_and_factor_matches_har() -> None:
    # HAR: 12.34 = exact 5.00 + exact 2.50 + factor 2 + factor 1 → 3.23 + 1.61
    shares = build_shares_attributes(
        total_fractional=1234,
        currency="EUR",
        shares=[
            {"member_id": "a", "exact_euros": "5.00"},
            {"member_id": "b", "exact_euros": "2.50"},
            {"member_id": "c", "factor": 2},
            {"member_id": "d", "factor": 1},
        ],
    )
    by_member = {row["member_id"]: row for row in shares}
    assert by_member["a"]["meta"] == {"type": "exact", "multiplier": 0}
    assert by_member["a"]["source_amount"]["fractional"] == 500
    assert by_member["b"]["source_amount"]["fractional"] == 250
    assert by_member["c"]["meta"] == {"type": "factor", "multiplier": 2}
    assert by_member["c"]["source_amount"]["fractional"] == 323
    assert by_member["d"]["meta"] == {"type": "factor", "multiplier": 1}
    assert by_member["d"]["source_amount"]["fractional"] == 161
    assert sum(r["source_amount"]["fractional"] for r in shares) == 1234


def test_exact_plus_percent_remainder() -> None:
    shares = build_shares_attributes(
        total_fractional=1000,
        currency="EUR",
        shares=[
            {"member_id": "a", "exact_fractional": 200},
            {"member_id": "b", "percent": 0.5},
            {"member_id": "c", "percent": 0.5},
        ],
    )
    by_member = {row["member_id"]: row for row in shares}
    assert by_member["a"]["meta"]["type"] == "exact"
    assert by_member["b"]["source_amount"]["fractional"] == 400
    assert by_member["c"]["source_amount"]["fractional"] == 400


def test_equal_shares() -> None:
    shares = build_equal_shares(
        total_fractional=100,
        currency="EUR",
        member_ids=["a", "b"],
    )
    assert [r["source_amount"]["fractional"] for r in shares] == [50, 50]
    assert all(r["meta"]["type"] == "factor" for r in shares)


def test_raw_shares_passthrough() -> None:
    raw = [
        {
            "id": "a",
            "member_id": "a",
            "meta": {"type": "exact", "multiplier": 0},
            "source_amount": {"fractional": 100, "currency": "EUR"},
        }
    ]
    assert build_shares_attributes(total_fractional=100, currency="EUR", shares=raw) == raw


def test_rejects_mixed_factor_and_percent() -> None:
    with pytest.raises(ValueError, match="cannot mix"):
        build_shares_attributes(
            total_fractional=100,
            currency="EUR",
            shares=[
                {"member_id": "a", "factor": 1},
                {"member_id": "b", "percent": 0.5},
            ],
        )


def test_rejects_exact_over_total() -> None:
    with pytest.raises(ValueError, match="exceed"):
        build_shares_attributes(
            total_fractional=100,
            currency="EUR",
            shares=[
                {"member_id": "a", "exact_fractional": 80},
                {"member_id": "b", "exact_fractional": 30},
            ],
        )
