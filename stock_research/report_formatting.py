from __future__ import annotations

from typing import Any


MONEY_FIELDS = {"latest_price", "analyst_target_price", "fifty_two_week_low", "fifty_two_week_high"}
LARGE_MONEY_FIELDS = {"market_cap", "revenue_ttm"}
RATIO_FIELDS = {"pe_ratio", "forward_pe", "peg_ratio", "price_to_sales_ttm", "ev_to_ebitda_ttm", "price_to_book_ratio", "beta"}
PERCENT_FIELDS = {
    "profit_margin",
    "operating_margin_ttm",
    "quarterly_revenue_growth_yoy",
    "quarterly_earnings_growth_yoy",
    "analyst_target_implied_upside",
    "range_position",
}
PER_SHARE_FIELDS = {"free_cash_flow_per_share_ttm"}


def format_financial_value(key: str, value: Any) -> str:
    if value is None:
        return "unknown"
    if key in LARGE_MONEY_FIELDS:
        return format_large_money(value)
    if key in MONEY_FIELDS:
        return format_money(value)
    if key in PERCENT_FIELDS:
        return format_percent(value)
    if key in RATIO_FIELDS:
        return format_ratio(value)
    if key in PER_SHARE_FIELDS:
        return format_money(value)
    return format_plain_value(value)


def format_large_money(value: Any) -> str:
    number = numeric(value)
    if number is None:
        return str(value)
    abs_value = abs(number)
    if abs_value >= 1_000_000_000_000:
        return f"${number / 1_000_000_000_000:.2f}T"
    if abs_value >= 1_000_000_000:
        return f"${number / 1_000_000_000:.2f}B"
    if abs_value >= 1_000_000:
        return f"${number / 1_000_000:.2f}M"
    return format_money(number)


def format_money(value: Any) -> str:
    number = numeric(value)
    if number is None:
        return str(value)
    if number < 0:
        return f"-${abs(number):,.2f}"
    return f"${number:,.2f}"


def format_percent(value: Any) -> str:
    number = numeric(value)
    if number is None:
        return str(value)
    return f"{number * 100:.2f}%"


def format_ratio(value: Any) -> str:
    number = numeric(value)
    if number is None:
        return str(value)
    return f"{number:.2f}x"


def format_plain_value(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def numeric(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
