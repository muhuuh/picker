from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .repo import RepoState
from .validation import parse_date


@dataclass(frozen=True)
class StaleItem:
    subject: str
    issue: str
    severity: str


def scan_stale_data(state: RepoState, today: date | None = None, max_age_days: int = 14) -> list[StaleItem]:
    current_date = today or date.today()
    items: list[StaleItem] = []

    for table_name, table in state.stock_tables.items():
        for row in table.rows:
            ticker = row.get("ticker", "").strip()
            if not ticker:
                continue
            last_updated = parse_date(row.get("date_last_updated", ""))
            if not last_updated:
                items.append(StaleItem(ticker, f"{table_name} row has no date_last_updated.", "medium"))
            elif (current_date - last_updated).days > max_age_days:
                items.append(
                    StaleItem(
                        ticker,
                        f"{table_name} row date_last_updated is older than {max_age_days} days.",
                        "medium",
                    )
                )

            next_review = parse_date(row.get("next_review_date", ""))
            if next_review and next_review <= current_date:
                items.append(StaleItem(ticker, f"{table_name} next_review_date is due.", "high"))

            for column in ["last_filing_checked", "last_news_checked", "last_sentiment_checked"]:
                checked = parse_date(row.get(column, ""))
                if checked and (current_date - checked).days > max_age_days:
                    items.append(StaleItem(ticker, f"{column} is older than {max_age_days} days.", "low"))

    for category, paths in state.stock_info_files.items():
        for path in paths:
            if path.name.upper() == "README.MD":
                continue
            content = path.read_text(encoding="utf-8")
            last_updated = parse_file_last_updated(content)
            subject = path.relative_to(state.root).as_posix()
            if not last_updated:
                items.append(StaleItem(subject, "company file has no Last updated date.", "medium"))
            elif (current_date - last_updated).days > max_age_days:
                items.append(StaleItem(subject, f"company file is older than {max_age_days} days.", "medium"))

    return items


def parse_file_last_updated(content: str) -> date | None:
    for line in content.splitlines()[:10]:
        if line.lower().startswith("last updated:"):
            return parse_date(line.split(":", 1)[1].strip())
    return None
