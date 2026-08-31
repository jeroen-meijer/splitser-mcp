"""Fractional cent amounts (1234 = EUR 12.34)."""

from __future__ import annotations


def euros_to_fractional(amount: str | float) -> int:
    """Euro decimal string to fractional cents."""
    if isinstance(amount, str):
        amount = amount.strip().replace(",", ".")
        value = float(amount)
    else:
        value = float(amount)
    return round(value * 100)


def fractional_to_euros(fractional: int) -> str:
    """Fractional cents to euro decimal string."""
    sign = "-" if fractional < 0 else ""
    absolute = abs(fractional)
    whole, cents = divmod(absolute, 100)
    return f"{sign}{whole}.{cents:02d}"


def money_dict(fractional: int, currency: str = "EUR") -> dict[str, object]:
    return {"fractional": fractional, "currency": currency}
