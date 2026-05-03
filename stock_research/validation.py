from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

from .repo import RepoState


CSV_SCHEMAS = {
    "current_holdings": [
        "ticker",
        "company_name",
        "exchange",
        "country",
        "currency",
        "sector",
        "industry",
        "status",
        "stock_info_file",
        "source",
        "price",
        "market_cap",
        "pe_ratio",
        "date_found",
        "date_last_updated",
        "next_review_date",
        "last_filing_checked",
        "last_news_checked",
        "last_sentiment_checked",
        "alert_level",
        "thesis_status",
        "notes",
    ],
    "monitoring": [
        "ticker",
        "company_name",
        "exchange",
        "country",
        "currency",
        "sector",
        "industry",
        "status",
        "stock_info_file",
        "source",
        "price",
        "market_cap",
        "pe_ratio",
        "date_found",
        "date_last_updated",
        "next_review_date",
        "last_filing_checked",
        "last_news_checked",
        "last_sentiment_checked",
        "alert_level",
        "watch_reason",
        "target_entry_criteria",
        "notes",
    ],
    "rejected": [
        "ticker",
        "company_name",
        "exchange",
        "country",
        "currency",
        "sector",
        "industry",
        "status",
        "stock_info_file",
        "source",
        "price",
        "market_cap",
        "pe_ratio",
        "date_found",
        "date_rejected",
        "next_eligible_review_date",
        "date_last_updated",
        "reject_reason",
        "reconsider_trigger",
        "notes",
    ],
}

DATE_COLUMNS = {
    "date_found",
    "date_last_updated",
    "next_review_date",
    "last_filing_checked",
    "last_news_checked",
    "last_sentiment_checked",
    "date_rejected",
    "next_eligible_review_date",
}

VALID_STATUSES = {"current_holding", "current_holdings", "monitoring", "rejected", ""}


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_repo_state(state: RepoState, today: date | None = None) -> ValidationReport:
    report = ValidationReport()
    current_date = today or date.today()

    for name, table in state.stock_tables.items():
        expected = CSV_SCHEMAS[name]
        if not table.path.exists():
            report.errors.append(f"Missing CSV: {relative(state.root, table.path)}")
            continue
        if table.fieldnames != expected:
            report.errors.append(
                f"{relative(state.root, table.path)} has unexpected headers. Expected {expected}, got {table.fieldnames}."
            )

        for index, row in enumerate(table.rows, start=2):
            validate_stock_row(state, name, row, index, report, current_date)

    for name, path in state.category_state_files.items():
        if not path.exists():
            report.errors.append(f"Missing category state file for {name}: {relative(state.root, path)}")

    if not (state.root / "docs/plans/human_research_requests.md").exists():
        report.errors.append("Missing human input queue: docs/plans/human_research_requests.md")
    if not (state.root / "strategy/research_priorities.md").exists():
        report.errors.append("Missing research priorities file: strategy/research_priorities.md")
    if not (state.root / "agents/human_review_queue.md").exists():
        report.errors.append("Missing human review queue: agents/human_review_queue.md")

    return report


def validate_stock_row(
    state: RepoState,
    table_name: str,
    row: dict[str, str],
    row_number: int,
    report: ValidationReport,
    today: date,
) -> None:
    ticker = row.get("ticker", "").strip()
    if not ticker and not any(value.strip() for value in row.values()):
        return

    status = row.get("status", "").strip()
    if status not in VALID_STATUSES:
        report.errors.append(f"{table_name} row {row_number}: invalid status '{status}'.")

    for column in DATE_COLUMNS:
        value = row.get(column, "").strip()
        if value and not parse_date(value):
            report.errors.append(f"{table_name} row {row_number}: invalid {column} '{value}', expected YYYY-MM-DD.")

    stock_info_file = row.get("stock_info_file", "").strip()
    if stock_info_file and not (state.root / stock_info_file).exists():
        report.warnings.append(f"{table_name} row {row_number}: stock_info_file does not exist: {stock_info_file}")

    if table_name == "rejected":
        validate_rejected_row(row, row_number, report, today)


def validate_rejected_row(row: dict[str, str], row_number: int, report: ValidationReport, today: date) -> None:
    rejected_at = parse_date(row.get("date_rejected", ""))
    eligible_at = parse_date(row.get("next_eligible_review_date", ""))
    if rejected_at and not eligible_at:
        report.warnings.append(f"rejected row {row_number}: missing next_eligible_review_date.")
    if rejected_at and eligible_at and eligible_at < rejected_at + timedelta(days=42):
        report.errors.append(
            f"rejected row {row_number}: next_eligible_review_date must be at least 6 weeks after date_rejected."
        )
    if rejected_at and eligible_at and eligible_at <= today:
        report.warnings.append(f"rejected row {row_number}: cooldown has expired; candidate may be reviewed again.")


def parse_date(value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def relative(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
