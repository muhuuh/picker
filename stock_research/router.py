from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from .human import append_human_request, classify_request
from .markdown_edit import append_markdown_table_row, append_section_entry
from .repo import load_first_table


@dataclass
class RouteResult:
    request_id: str
    request_type: str
    updated_paths: list[str] = field(default_factory=list)
    review_items: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def route_request(
    root: Path,
    request_text: str,
    priority: str = "medium",
    status: str = "queued_for_weekly_run",
    today: date | None = None,
) -> RouteResult:
    current_date = today or date.today()
    root = root.resolve()
    classification = classify_request(request_text)
    request_id = append_human_request(root, request_text, priority, status, current_date)
    result = RouteResult(request_id=request_id, request_type=classification.request_type)

    if classification.request_type == "stock_research":
        route_stock_research(root, request_id, request_text, classification.tickers, current_date, result)
    elif classification.request_type == "industry_research":
        route_market_research(root, "industries", "industry", request_id, request_text, priority, current_date, result)
    elif classification.request_type == "theme_tracking":
        route_market_research(root, "themes", "theme", request_id, request_text, priority, current_date, result)
    elif classification.request_type == "strategy_change":
        route_strategy_change(root, request_id, request_text, priority, current_date, result)
    elif classification.request_type == "alert_review":
        result.notes.append("Alert review request recorded; no target artifact needed until run summaries exist.")
    elif classification.request_type == "manual_run":
        route_manual_run(root, request_id, request_text, classification.tickers, current_date, result)
    elif classification.request_type == "stock_status_move":
        add_human_review_item(
            root,
            item=f"Review stock status move request: {request_text}",
            decision="Approve, reject, or clarify the requested stock status move.",
            priority=priority,
            related_files="stock_tracking/, docs/plans/human_research_requests.md",
            evidence=request_id,
            today=current_date,
        )
        result.review_items.append("stock status move approval")
        result.updated_paths.append("agents/human_review_queue.md")
    else:
        result.notes.append("Request recorded but no deterministic route was available.")

    return result


def route_stock_research(
    root: Path,
    request_id: str,
    request_text: str,
    tickers: list[str],
    today: date,
    result: RouteResult,
) -> None:
    if not tickers:
        result.notes.append("No uppercase ticker symbols detected; request remains in human input queue only.")
        return

    csv_path = root / "stock_tracking" / "monitoring" / "monitoring.csv"
    rows = read_csv_rows(csv_path)
    existing = {row.get("ticker", "").upper() for row in rows}
    fieldnames = read_csv_fieldnames(csv_path)

    for ticker in tickers:
        if ticker.upper() in existing:
            result.notes.append(f"{ticker} already exists in monitoring.csv; skipped CSV insert.")
            continue
        company_file = root / "stock_tracking" / "stock_info_files" / "monitoring" / f"{ticker}_pending.md"
        stock_info_rel = company_file.relative_to(root).as_posix()
        rows.append(
            {
                "ticker": ticker,
                "company_name": "",
                "exchange": "",
                "country": "",
                "currency": "",
                "sector": "",
                "industry": "",
                "status": "monitoring",
                "stock_info_file": stock_info_rel,
                "source": request_id,
                "price": "",
                "market_cap": "",
                "pe_ratio": "",
                "date_found": today.isoformat(),
                "date_last_updated": today.isoformat(),
                "next_review_date": next_saturday(today).isoformat(),
                "last_filing_checked": "",
                "last_news_checked": "",
                "last_sentiment_checked": "",
                "alert_level": "low",
                "watch_reason": request_text,
                "target_entry_criteria": "Research requested by user.",
                "notes": "",
            }
        )
        write_csv_rows(csv_path, fieldnames, rows)
        create_company_file(company_file, ticker, request_id, request_text, today)
        result.updated_paths.extend([csv_path.relative_to(root).as_posix(), stock_info_rel])


def create_company_file(path: Path, ticker: str, request_id: str, request_text: str, today: date) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""# {ticker} Pending Company Name

Last updated: {today.isoformat()}

## Company Snapshot

- Ticker: {ticker}
- Company name:
- Exchange:
- Country:
- Currency:
- Sector:
- Industry:
- Market cap:
- Current status: monitoring
- Stock tracking row: stock_tracking/monitoring/monitoring.csv
- Primary sources: {request_id}

## Status Dates

- Date found: {today.isoformat()}
- Date last updated: {today.isoformat()}
- Next review date: {next_saturday(today).isoformat()}
- Date rejected:
- Next eligible review date:

## Current Opinion

- Summary: Research requested by user; no analysis completed yet.
- Confidence: low
- Current decision: monitoring
- What would change our mind:

## Thesis

- Why this company is interesting: {request_text}
- What must be true:
- Main upside drivers:
- Main downside risks:

## Filings

| Date | Filing | Source | Key points | Follow-up |
| --- | --- | --- | --- | --- |
| TODO | TODO | TODO | TODO | TODO |

## Financials

- Revenue growth:
- Gross margin:
- Operating margin:
- Free cash flow:
- Cash and equivalents:
- Debt:
- Valuation:
- Dilution / share count:
- Notes:

## Developments

| Date | Development | Source | Impact | Confidence |
| --- | --- | --- | --- | --- |
| TODO | TODO | TODO | TODO | TODO |

## Sentiment

- X.com / community sentiment:
- News sentiment:
- Analyst / expert tone:
- Noise caveats:

## Risks and Red Flags

- Accounting:
- Balance sheet:
- Competition:
- Regulation / legal:
- Customer concentration:
- Cyclicality:
- Governance:
- Other:

## Open Questions

- Verify company identity, exchange, country, sector, and strategy fit.

## Next Actions

- [ ] Run initial company research.

## Source Log

| Date accessed | Source | URL / artifact | Notes |
| --- | --- | --- | --- |
| {today.isoformat()} | Human request | {request_id} | {request_text} |

## Change Log

| Date | Updated by | Summary | Sources |
| --- | --- | --- | --- |
| {today.isoformat()} | Codex | Created monitoring file from human request. | {request_id} |
"""
    path.write_text(content, encoding="utf-8")


def route_market_research(
    root: Path,
    folder_name: str,
    priority_type: str,
    request_id: str,
    request_text: str,
    priority: str,
    today: date,
    result: RouteResult,
) -> None:
    title = derive_topic_title(request_text)
    slug = slugify(title)
    research_path = root / "market_research" / folder_name / f"{slug}.md"
    if not research_path.exists():
        research_path.write_text(
            f"""# {title}

Last updated: {today.isoformat()}

## Current View

- Research requested by user; no analysis completed yet.

## Original Request

- {request_text}

## Why It Matters

- TODO: explain strategy relevance after research.

## Candidate Stocks

| Ticker | Company | Exchange | Country | Why surfaced | Next action |
| --- | --- | --- | --- | --- | --- |
| TODO | TODO | TODO | TODO | TODO | TODO |

## Next Actions

- [ ] Run {priority_type} research.
- [ ] Identify candidate stocks.
- [ ] Update strategy fit and source log.

## Source Log

| Date accessed | Source | URL / artifact | Notes |
| --- | --- | --- | --- |
| {today.isoformat()} | Human request | {request_id} | {request_text} |

## Change Log

- {today.isoformat()}: Created from human request {request_id}.
""",
            encoding="utf-8",
        )
    else:
        append_section_entry(
            research_path,
            "## Human Request Log",
            f"- {today.isoformat()} ({request_id}): {request_text}",
        )

    result.updated_paths.append(research_path.relative_to(root).as_posix())
    add_research_priority(root, title, priority_type, priority, request_text, research_path, today)
    result.updated_paths.append("strategy/research_priorities.md")


def route_strategy_change(root: Path, request_id: str, request_text: str, priority: str, today: date, result: RouteResult) -> None:
    strategy_path = root / "strategy" / "investment_strategy.md"
    append_section_entry(strategy_path, "## User Strategy Inputs", f"- {today.isoformat()} ({request_id}): {request_text}")
    add_human_review_item(
        root,
        item=f"Review strategy input: {request_text}",
        decision="Decide whether and how to promote this input into strategy rules.",
        priority=priority,
        related_files="strategy/investment_strategy.md, docs/plans/human_research_requests.md",
        evidence=request_id,
        today=today,
    )
    result.updated_paths.extend(["strategy/investment_strategy.md", "agents/human_review_queue.md"])
    result.review_items.append("strategy change approval")


def route_manual_run(root: Path, request_id: str, request_text: str, tickers: list[str], today: date, result: RouteResult) -> None:
    run_dir = root / "agents" / "runs" / f"{today.isoformat()}_manual-{request_id.lower()}"
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "manifest_version": 1,
        "manifest_id": f"manual_{request_id}",
        "run_type": "manual",
        "run_date": today.isoformat(),
        "request_id": request_id,
        "request": request_text,
        "tickers": tickers,
        "status": "planned",
        "tasks": [{"id": "manual_research_request", "kind": "manual", "reason": request_text}],
    }
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result.updated_paths.append(manifest_path.relative_to(root).as_posix())


def add_research_priority(
    root: Path,
    title: str,
    priority_type: str,
    priority: str,
    request_text: str,
    related_path: Path,
    today: date,
) -> None:
    path = root / "strategy" / "research_priorities.md"
    priority_id = next_research_priority_id(path)
    row = [
        priority_id,
        title,
        priority_type,
        "US, Europe",
        priority,
        "active",
        request_text,
        "weekly",
        today.isoformat(),
        next_saturday(today).isoformat(),
        related_path.relative_to(root).as_posix(),
        "Added from human request.",
    ]
    append_markdown_table_row(path, "| Priority ID | Topic | Type |", row)


def add_human_review_item(
    root: Path,
    item: str,
    decision: str,
    priority: str,
    related_files: str,
    evidence: str,
    today: date,
) -> None:
    path = root / "agents" / "human_review_queue.md"
    review_id = next_human_review_id(path)
    row = [review_id, today.isoformat(), item, decision, priority, "open", related_files, evidence, ""]
    append_markdown_table_row(path, "| ID | Date Added | Item |", row)


def next_research_priority_id(path: Path) -> str:
    return next_id(path, "Priority ID", r"RP-(\d+)", "RP")


def next_human_review_id(path: Path) -> str:
    return next_id(path, "ID", r"HRQ-(\d+)", "HRQ")


def next_id(path: Path, column: str, pattern: str, prefix: str) -> str:
    rows = load_first_table(path)
    max_number = 0
    for row in rows:
        match = re.match(pattern, row.get(column, ""))
        if match:
            max_number = max(max_number, int(match.group(1)))
    return f"{prefix}-{max_number + 1:04d}"


def derive_topic_title(request_text: str) -> str:
    cleaned = re.sub(r"\b(please|look into|find interesting stocks|research|track|include|from now on)\b", "", request_text, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    if not cleaned:
        return "Untitled Research Request"
    return cleaned[:80].strip().title()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    return slug[:80] or "untitled"


def next_saturday(value: date) -> date:
    return value + timedelta(days=(5 - value.weekday()) % 7)


def read_csv_fieldnames(path: Path) -> list[str]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        return next(reader)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [{key: value or "" for key, value in row.items() if key is not None} for row in reader]


def write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
