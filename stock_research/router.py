from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from .human import append_human_request, classify_request
from .markdown_edit import append_markdown_table_row, append_section_entry
from .research_profiles import assert_write_allowed, build_research_run_spec, write_research_run_spec
from .repo import load_first_table


@dataclass
class RouteResult:
    request_id: str
    request_type: str
    request_status: str = ""
    profile_id: str = ""
    run_spec_path: str = ""
    updated_paths: list[str] = field(default_factory=list)
    review_items: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def route_request(
    root: Path,
    request_text: str,
    priority: str = "medium",
    status: str = "auto",
    today: date | None = None,
) -> RouteResult:
    current_date = today or date.today()
    root = root.resolve()
    classification = classify_request(request_text)
    request_status = resolve_request_status(status, classification.request_type)
    request_id = append_human_request(root, request_text, priority, request_status, current_date)
    result = RouteResult(
        request_id=request_id,
        request_type=classification.request_type,
        request_status=request_status,
    )

    if classification.request_type == "stock_research":
        result.profile_id = "company_deep_research"
        route_stock_research(root, request_id, request_text, classification.tickers, current_date, result)
    elif classification.request_type == "industry_research":
        result.profile_id = "industry_deep_research"
        route_market_research(root, "industries", "industry", request_id, request_text, priority, current_date, result)
    elif classification.request_type == "theme_tracking":
        result.profile_id = "industry_deep_research"
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


def resolve_request_status(status: str, request_type: str) -> str:
    normalized = str(status or "").strip().lower()
    if normalized and normalized != "auto":
        return normalized
    if request_type in {"stock_research", "industry_research", "theme_tracking"}:
        return "planned_on_demand"
    return "queued_for_weekly_run"


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
    run_id = f"{today.isoformat()}_company-deep-{request_id.lower()}"
    spec = build_research_run_spec(
        "company_deep_research",
        run_id=run_id,
        request_id=request_id,
        request=request_text,
        subjects=(
            {"subject_type": "company", "subject_id": ticker.upper(), "label": ticker.upper()}
            for ticker in tickers
        ),
    )
    spec_path = write_research_run_spec(root, spec)
    relative_spec_path = spec_path.relative_to(root).as_posix()
    result.run_spec_path = relative_spec_path
    result.updated_paths.append(relative_spec_path)
    result.notes.append(
        "Research-only request planned without changing holdings or monitoring. "
        "Use an explicit stock-status request and approval flow to change portfolio membership."
    )


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

- X via xAI/Grok / community sentiment:
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
    run_id = f"{today.isoformat()}_industry-deep-{request_id.lower()}"
    spec = build_research_run_spec(
        "industry_deep_research",
        run_id=run_id,
        request_id=request_id,
        request=request_text,
        subjects=({"subject_type": priority_type, "subject_id": slug, "label": title},),
    )
    assert_write_allowed(spec.profile, "reader_reports")
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
    spec_path = write_research_run_spec(root, spec)
    relative_spec_path = spec_path.relative_to(root).as_posix()
    result.run_spec_path = relative_spec_path
    result.updated_paths.append(relative_spec_path)
    result.notes.append(
        "On-demand industry/theme research does not create a recurring strategy priority. "
        "Recurring coverage requires a separate explicit strategy request."
    )


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
