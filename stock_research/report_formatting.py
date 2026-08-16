from __future__ import annotations

from typing import Any
import re

from .text_excerpt import complete_sentence_excerpt


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


def compact_complete_text(value: str, max_length: int = 600) -> str:
    """Return a complete display excerpt without hiding source truncation."""
    compact = " ".join(str(value or "").split())
    compact = re.sub(r"\[\[\d+\]\](?:\([^)]+\))?", "", compact)
    compact = re.sub(r"(?<!\!)\[(\d+)\](?!\()", "", compact)
    compact = repair_common_mojibake(compact)
    return complete_sentence_excerpt(
        compact,
        max_length,
        allow_complete_phrase=True,
    ).text


def repair_common_mojibake(value: str) -> str:
    value = repair_latin1_mojibake(value)
    replacements = {
        "\u00e2\u20ac\u2122": "'",
        "\u00e2\u20ac\u0153": '"',
        "\u00e2\u20ac\u009d": '"',
        "\u00e2\u20ac\u201c": "-",
        "\u00e2\u20ac\u201d": "-",
        "\u00c2\u00a0": " ",
        "Ã—": "x",
        "Ã©": "e",
        "Ã¨": "e",
        "Ã¡": "a",
        "Ã ": "a",
        "Ã¼": "u",
        "Ã¶": "o",
        "Ã¤": "a",
        "â€™": "'",
        "â€œ": '"',
        "â€": '"',
        "â€“": "-",
        "â€”": "-",
        "â€¦": ".",
    }
    replacements.update(
        {
            "\u00e2\u20ac\u00a2": "-",
            "\u00e2\u2020\u2019": "->",
            "\u00e2\u201e\u00a2": "",
            "\u00c2\u00ae": "",
            "\u2022": "-",
            "\u2192": "->",
            "\u2122": "",
            "\u00ae": "",
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2013": "-",
            "\u2014": "-",
            "\u00c3\u00bc": "u",
            "\u00c3\u00b6": "o",
            "\u00c3\u00a4": "a",
            "\u00c3\u00a9": "e",
            "\u00c3\u00a8": "e",
            "\u00c3\u00a1": "a",
            "\u00c2": "",
        }
    )
    for bad, good in replacements.items():
        value = value.replace(bad, good)
    value = value.replace("\u00d7", "x")
    value = re.sub(r"(?<=\d)\?\?(?=\s*(?:P/[ESB]|P/E|P/S|PE|EV|multiple|margin|revenue))", "x", value)
    return value


def repair_latin1_mojibake(value: str) -> str:
    if not any(marker in value for marker in ("\u00c2", "\u00c3", "\u00e2", "\ufffd")):
        return value
    try:
        repaired = value.encode("cp1252").decode("utf-8")
    except UnicodeError:
        return value
    return repaired if mojibake_score(repaired) < mojibake_score(value) else value


def mojibake_score(value: str) -> int:
    return len(re.findall(r"[\u00c2\u00c3\u00e2\ufffd]", value))


def markdown_link(label: str, url: str) -> str:
    cleaned_label = str(label or "source").replace("[", "(").replace("]", ")").strip()
    cleaned_url = str(url or "").strip()
    return f"[{cleaned_label}]({cleaned_url})" if cleaned_url else cleaned_label


def numeric(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
