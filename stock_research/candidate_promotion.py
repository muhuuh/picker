from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from stock_research.agent_runtime.proposal_review import normalize_ascii
from stock_research.candidate_followup import (
    CANDIDATE_REVIEW_REPORT,
    CANDIDATE_VERIFICATION_MANIFEST,
    candidate_group_id_from_evidence,
    load_candidate_groups,
    matching_human_review_rows,
)
from stock_research.repo import find_repo_root, read_csv_table


CANDIDATE_PROMOTION_REPORT = "candidate_promotion_report.md"
MONITORING_COLUMNS = [
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
]


@dataclass
class CandidatePromotionItem:
    review_item_id: str
    candidate_group_id: str
    candidate: str
    ticker: str = ""
    decision_kind: str = ""
    review_status: str = ""
    status: str = "blocked"
    findings: list[str] = field(default_factory=list)
    written_paths: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CandidatePromotionResult:
    run_id: str
    generated_at: str
    status: str
    review_id: str
    item: CandidatePromotionItem | None = None
    findings: list[str] = field(default_factory=list)
    written_paths: list[str] = field(default_factory=list)


def build_candidate_monitoring_promotion(
    *,
    root: Path | None = None,
    run_id: str,
    review_id: str,
    ticker: str = "",
    current_date: date | None = None,
    write: bool = False,
) -> CandidatePromotionResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    if not review_id:
        return CandidatePromotionResult(
            run_id=run_id,
            generated_at=today.isoformat(),
            status="blocked",
            review_id=review_id,
            findings=["A human-review row id is required for candidate promotion."],
        )

    market_dir = repo_root / "agents" / "runs" / run_id / "market_research"
    review_report_path = market_dir / CANDIDATE_REVIEW_REPORT
    if not review_report_path.exists():
        return CandidatePromotionResult(
            run_id=run_id,
            generated_at=today.isoformat(),
            status="blocked",
            review_id=review_id,
            findings=[f"Missing candidate review report: {review_report_path.relative_to(repo_root).as_posix()}"],
        )

    rows = matching_human_review_rows(repo_root, run_id, review_id)
    if not rows:
        return CandidatePromotionResult(
            run_id=run_id,
            generated_at=today.isoformat(),
            status="blocked",
            review_id=review_id,
            findings=[f"No candidate-review human-review row found for review id: {review_id}"],
        )

    row = rows[0]
    group_id = candidate_group_id_from_evidence(row.get("Evidence / Run Link", ""))
    group = load_candidate_groups(review_report_path).get(group_id)
    if not group:
        return CandidatePromotionResult(
            run_id=run_id,
            generated_at=today.isoformat(),
            status="blocked",
            review_id=review_id,
            findings=[f"Missing candidate group {group_id} in candidate review report."],
        )

    item = build_promotion_item(row, group, ticker)
    evaluate_promotion_readiness(repo_root, run_id, item)
    status = item.status if item.status in {"ready_to_promote", "already_promoted"} else "blocked"

    written_paths: list[str] = []
    if write and item.status == "ready_to_promote":
        written_paths.extend(write_monitoring_artifacts(repo_root, run_id, today, item))
        item.status = "promoted"
        status = "promoted"
    elif write and item.status == "already_promoted":
        report_path = write_candidate_promotion_report(repo_root, run_id, today, "already_promoted", item)
        written_paths.append(report_path.relative_to(repo_root).as_posix())
        status = "already_promoted"
    elif write:
        report_path = write_candidate_promotion_report(repo_root, run_id, today, status, item)
        written_paths.append(report_path.relative_to(repo_root).as_posix())

    item.written_paths.extend(written_paths)
    return CandidatePromotionResult(
        run_id=run_id,
        generated_at=today.isoformat(),
        status=status,
        review_id=review_id,
        item=item,
        findings=item.findings,
        written_paths=written_paths,
    )


def build_promotion_item(row: dict[str, str], group: dict[str, str], requested_ticker: str = "") -> CandidatePromotionItem:
    tickers = [value.strip().upper() for value in group.get("Tickers", "").split(",") if value.strip()]
    ticker = requested_ticker.strip().upper()
    findings: list[str] = []
    if ticker and ticker not in tickers:
        findings.append(f"Requested ticker {ticker} is not in candidate group tickers: {', '.join(tickers) or 'none'}.")
    elif ticker:
        selected_ticker = ticker
    elif len(tickers) == 1:
        selected_ticker = tickers[0]
    else:
        selected_ticker = ""
        findings.append("Candidate group has multiple or zero tickers; pass --ticker after choosing the listing/share class.")

    return CandidatePromotionItem(
        review_item_id=row.get("ID", ""),
        candidate_group_id=group.get("Group ID", ""),
        candidate=normalize_ascii(group.get("Candidate", "")),
        ticker=selected_ticker,
        decision_kind=normalize_ascii(group.get("Decision Kind", "")),
        review_status=normalize_ascii(row.get("Status", "")),
        findings=findings,
    )


def evaluate_promotion_readiness(repo_root: Path, run_id: str, item: CandidatePromotionItem) -> None:
    already_monitoring = False
    status = item.review_status.lower()
    if status != "approved":
        item.findings.append(f"Human-review item {item.review_item_id} is '{status or 'unknown'}', not 'approved'.")
    if item.decision_kind != "monitoring_candidate":
        item.findings.append(
            f"Candidate review decision is '{item.decision_kind}', not 'monitoring_candidate'; this approval is for verification/follow-up, not monitoring promotion."
        )
    if not item.ticker:
        item.findings.append("No single ticker selected for monitoring promotion.")
    if item.ticker:
        already_monitoring = ticker_exists_in_csv(repo_root / "stock_tracking" / "monitoring" / "monitoring.csv", item.ticker)
        item.findings.extend(existing_blocking_status_findings(repo_root, item.ticker))
        item.findings.extend(verification_artifact_findings(repo_root, run_id, item.ticker))
    if item.findings:
        item.status = "blocked"
    elif already_monitoring:
        item.status = "already_promoted"
    else:
        item.status = "ready_to_promote"


def existing_blocking_status_findings(repo_root: Path, ticker: str) -> list[str]:
    findings: list[str] = []
    holdings = read_csv_table(repo_root / "stock_tracking" / "current_holdings" / "current_holdings.csv")
    rejected = read_csv_table(repo_root / "stock_tracking" / "rejected" / "rejected.csv")
    if any(row.get("ticker", "").upper() == ticker.upper() for row in holdings.rows):
        findings.append(f"{ticker} already exists in current_holdings; monitoring promotion is not the correct status move.")
    for row in rejected.rows:
        if row.get("ticker", "").upper() != ticker.upper():
            continue
        next_eligible = row.get("next_eligible_review_date", "")
        if next_eligible:
            findings.append(f"{ticker} exists in rejected.csv with next eligible review date {next_eligible}; explicit cooldown override is required.")
        else:
            findings.append(f"{ticker} exists in rejected.csv; explicit rejection review is required before promotion.")
    return findings


def ticker_exists_in_csv(path: Path, ticker: str) -> bool:
    table = read_csv_table(path)
    return any(row.get("ticker", "").upper() == ticker.upper() for row in table.rows)


def verification_artifact_findings(repo_root: Path, run_id: str, ticker: str) -> list[str]:
    findings: list[str] = []
    market_dir = repo_root / "agents" / "runs" / run_id / "market_research"
    manifest_path = market_dir / CANDIDATE_VERIFICATION_MANIFEST
    if not manifest_path.exists():
        return [f"Missing verification manifest: {manifest_path.relative_to(repo_root).as_posix()}"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Verification manifest is invalid JSON: {exc}"]

    task_tickers = {
        str(task.get("subject_id", "")).upper()
        for section in ("provider_tasks", "analysis_tasks")
        for task in manifest.get(section, [])
        if isinstance(task, dict)
    }
    if ticker.upper() not in task_tickers:
        findings.append(f"Verification manifest has no provider/analysis tasks for {ticker}.")

    required_reports = [
        repo_root / "agents" / "runs" / run_id / "reports" / "company_news_specialist" / f"{ticker}_company_news_review.md",
        repo_root / "agents" / "runs" / run_id / "reports" / "financial_data_specialist" / f"{ticker}_financial_review.md",
    ]
    for path in required_reports:
        if not path.exists():
            findings.append(f"Missing verification report: {path.relative_to(repo_root).as_posix()}")
    return findings


def write_monitoring_artifacts(repo_root: Path, run_id: str, today: date, item: CandidatePromotionItem) -> list[str]:
    written: list[str] = []
    monitoring_path = repo_root / "stock_tracking" / "monitoring" / "monitoring.csv"
    stock_info_rel = f"stock_tracking/stock_info_files/monitoring/{safe_stock_file_name(item.ticker)}.md"
    monitoring_path.parent.mkdir(parents=True, exist_ok=True)
    stock_info_path = repo_root / stock_info_rel
    stock_info_path.parent.mkdir(parents=True, exist_ok=True)

    appended = append_monitoring_row(monitoring_path, run_id, today, item, stock_info_rel)
    if appended:
        written.append(monitoring_path.relative_to(repo_root).as_posix())
    if not stock_info_path.exists():
        stock_info_path.write_text(format_company_file(item, today, stock_info_rel, run_id), encoding="utf-8")
        written.append(stock_info_path.relative_to(repo_root).as_posix())

    report_path = write_candidate_promotion_report(repo_root, run_id, today, "promoted", item)
    written.append(report_path.relative_to(repo_root).as_posix())
    return written


def append_monitoring_row(path: Path, run_id: str, today: date, item: CandidatePromotionItem, stock_info_rel: str) -> bool:
    table = read_csv_table(path)
    fieldnames = table.fieldnames or MONITORING_COLUMNS
    if "ticker" not in fieldnames:
        fieldnames = MONITORING_COLUMNS
    if any(row.get("ticker", "").upper() == item.ticker.upper() for row in table.rows):
        return False

    row = {field: "" for field in fieldnames}
    row.update(
        {
            "ticker": item.ticker,
            "company_name": item.candidate,
            "status": "monitoring",
            "stock_info_file": stock_info_rel,
            "source": f"candidate promotion from agents/runs/{run_id}/market_research/candidate_review.md#{item.candidate_group_id}",
            "date_found": today.isoformat(),
            "date_last_updated": today.isoformat(),
            "next_review_date": (today + timedelta(days=7)).isoformat(),
            "alert_level": "medium",
            "watch_reason": f"Promoted from market-discovery review {item.review_item_id} after verification artifacts existed.",
            "target_entry_criteria": "Needs full company research thesis before any investment decision.",
            "notes": f"Source run: candidate review {item.review_item_id}.",
        }
    )
    rows = [normalize_csv_row(existing, fieldnames) for existing in table.rows]
    rows.append(row)
    write_csv_rows(path, fieldnames, rows)
    return True


def format_company_file(item: CandidatePromotionItem, today: date, stock_info_rel: str, run_id: str) -> str:
    return "\n".join(
        [
            f"# {item.ticker} {item.candidate}",
            "",
            f"Last updated: {today.isoformat()}",
            "",
            "## Company Snapshot",
            "",
            f"- Ticker: {item.ticker}",
            f"- Company name: {item.candidate}",
            "- Exchange:",
            "- Country:",
            "- Currency:",
            "- Sector:",
            "- Industry:",
            "- Market cap:",
            "- Current status: monitoring",
            "- Stock tracking row: `stock_tracking/monitoring/monitoring.csv`",
            f"- Primary sources: `agents/runs/{run_id}/market_research/candidate_review.md#{item.candidate_group_id}`, `agents/runs/{run_id}/market_research/{CANDIDATE_VERIFICATION_MANIFEST}`",
            "",
            "## Status Dates",
            "",
            f"- Date found: {today.isoformat()}",
            f"- Date last updated: {today.isoformat()}",
            f"- Next review date: {(today + timedelta(days=7)).isoformat()}",
            "- Date rejected:",
            "- Next eligible review date:",
            "",
            "## Current Opinion",
            "",
            "- Summary: Promoted to monitoring from market-discovery review after approval and required verification artifacts existed.",
            "- Confidence: low",
            "- Current decision: monitoring; not an investment recommendation.",
            "- What would change our mind: Company research identifies weak strategy fit, poor financial quality, unresolved source conflicts, or user rejects the candidate.",
            "",
            "## Thesis",
            "",
            "- Why this company is interesting: Surfaced by market-discovery workflow.",
            "- What must be true: Follow-up company research confirms strategic fit and material evidence quality.",
            "- Main upside drivers:",
            "- Main downside risks:",
            "",
            "## Filings",
            "",
            "| Date | Filing | Source | Key points | Follow-up |",
            "| --- | --- | --- | --- | --- |",
            f"| {today.isoformat()} | Candidate verification | `agents/runs/{run_id}/market_research/{CANDIDATE_VERIFICATION_MANIFEST}` | Verification manifest existed before promotion. | Review filing artifacts before thesis upgrade. |",
            "",
            "## Financials",
            "",
            "- Revenue growth:",
            "- Gross margin:",
            "- Operating margin:",
            "- Free cash flow:",
            "- Cash and equivalents:",
            "- Debt:",
            "- Valuation:",
            "- Dilution / share count:",
            "- Notes: Use the candidate verification financial review before making thesis claims.",
            "",
            "## Developments",
            "",
            "| Date | Development | Source | Impact | Confidence |",
            "| --- | --- | --- | --- | --- |",
            f"| {today.isoformat()} | Added to monitoring from candidate discovery. | `agents/runs/{run_id}/market_research/candidate_review.md#{item.candidate_group_id}` | Starts recurring tracking. | medium |",
            "",
            "## Sentiment",
            "",
            "- X via xAI/Grok / community sentiment: See candidate verification artifacts; treat as social signal only.",
            "- News sentiment: See company-news verification report.",
            "- Analyst / expert tone:",
            "- Noise caveats:",
            "",
            "## Risks and Red Flags",
            "",
            "- Accounting:",
            "- Balance sheet:",
            "- Competition:",
            "- Regulation / legal:",
            "- Customer concentration:",
            "- Cyclicality:",
            "- Governance:",
            "- Other:",
            "",
            "## Open Questions",
            "",
            "- Complete full company-research pass and decide whether this remains a real monitoring candidate.",
            "",
            "## Next Actions",
            "",
            "- [ ] Run full company research in the next manual or weekly workflow.",
            "- [ ] Update thesis, risks, financials, and source log from verification artifacts.",
            "",
            "## Source Log",
            "",
            "| Date accessed | Source | URL / artifact | Notes |",
            "| --- | --- | --- | --- |",
            f"| {today.isoformat()} | Candidate review | `agents/runs/{run_id}/market_research/candidate_review.md#{item.candidate_group_id}` | Human-approved monitoring candidate. |",
            f"| {today.isoformat()} | Candidate verification manifest | `agents/runs/{run_id}/market_research/{CANDIDATE_VERIFICATION_MANIFEST}` | Required before promotion. |",
            "",
            "## Change Log",
            "",
            "| Date | Updated by | Summary | Sources |",
            "| --- | --- | --- | --- |",
            f"| {today.isoformat()} | deterministic candidate promotion writer | Created monitoring company file. | `agents/runs/{run_id}/market_research/{CANDIDATE_PROMOTION_REPORT}` |",
        ]
    ).rstrip() + "\n"


def write_candidate_promotion_report(repo_root: Path, run_id: str, today: date, status: str, item: CandidatePromotionItem) -> Path:
    market_dir = repo_root / "agents" / "runs" / run_id / "market_research"
    market_dir.mkdir(parents=True, exist_ok=True)
    path = market_dir / CANDIDATE_PROMOTION_REPORT
    path.write_text(format_candidate_promotion_report(run_id, today, status, item), encoding="utf-8")
    return path


def format_candidate_promotion_report(run_id: str, today: date, status: str, item: CandidatePromotionItem) -> str:
    lines = [
        f"# Candidate Promotion Report: {run_id}",
        "",
        f"Generated: {today.isoformat()}",
        f"Status: {status}",
        "",
        "## Candidate",
        "",
        f"- Review item: {item.review_item_id}",
        f"- Candidate group: {item.candidate_group_id}",
        f"- Company: {item.candidate}",
        f"- Ticker: {item.ticker or 'not selected'}",
        f"- Decision kind: {item.decision_kind}",
        f"- Review status: {item.review_status}",
        "",
        "## Findings",
        "",
    ]
    if item.findings:
        lines.extend(f"- {finding}" for finding in item.findings)
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Outcome",
            "",
            "- `promoted` means a monitoring CSV row and company file were created or already present.",
            "- `already_promoted` means the ticker is already in monitoring and no duplicate row was written.",
            "- `blocked` means no monitoring state was changed.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def normalize_csv_row(row: dict[str, str], fieldnames: list[str]) -> dict[str, str]:
    return {field: row.get(field, "") for field in fieldnames}


def write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def safe_stock_file_name(ticker: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", ticker.upper()).strip("_")
    return cleaned or "UNKNOWN"


def candidate_promotion_to_dict(result: CandidatePromotionResult) -> dict[str, Any]:
    return {
        "run_id": result.run_id,
        "generated_at": result.generated_at,
        "status": result.status,
        "review_id": result.review_id,
        "item": asdict(result.item) if result.item else None,
        "findings": result.findings,
        "written_paths": result.written_paths,
    }
