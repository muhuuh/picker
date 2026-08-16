from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from stock_research.agent_runtime.outputs import CandidateLead
from stock_research.agent_runtime.proposal_review import normalize_ascii
from stock_research.candidate_followup import build_candidate_verification_followup, candidate_followup_to_dict
from stock_research.candidate_review import build_candidate_review, candidate_review_to_dict
from stock_research.human_review_decisions import HumanReviewDecision, apply_human_review_decisions
from stock_research.repo import find_repo_root, read_csv_table


SHEET_ID = "16S9NXkIi4IH6fPHe3DMpxvtjknzzRIjyxW2XjJp6Jr0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
SHEET_TAB = "Sheet1"

CANONICAL_HEADERS = [
    "Date",
    "Name",
    "Ticker",
    "Industry",
    "Mcap",
    "Forward PE",
    "P/S",
    "Forecast",
    "Score",
    "available",
    "action",
    "Comment",
    "Processing status",
    "Repo link",
    "Last checked",
]

AVAILABLE_OPTIONS = ["yes", "no"]
SCORE_OPTIONS = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]
ACTION_OPTIONS = ["research", "add to monitoring", "buy candidate", "bought", "ignore", "rejected"]
PROCESSING_STATUS_OPTIONS = ["not processed", "in research", "done", "needs fix"]
DEFAULT_SELECTED_ACTIONS = {"research"}


@dataclass(frozen=True)
class SheetIntakeRow:
    row_number: int
    date_added: str = ""
    name: str = ""
    ticker: str = ""
    industry: str = ""
    market_cap: str = ""
    forward_pe: str = ""
    price_to_sales: str = ""
    forecast: str = ""
    score: str = ""
    available: str = ""
    action: str = ""
    comment: str = ""
    processing_status: str = ""
    repo_link: str = ""
    last_checked: str = ""


@dataclass(frozen=True)
class SheetIntakeResult:
    run_id: str
    generated_at: str
    status: str
    selected_count: int
    skipped_count: int
    review_ids: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    written_paths: list[str] = field(default_factory=list)
    candidate_review: dict[str, Any] | None = None
    verification_followup: dict[str, Any] | None = None


def build_sheet_intake_candidate_review(
    *,
    root: Path | None = None,
    rows: list[dict[str, Any]] | list[list[Any]],
    run_id: str = "",
    selected_actions: set[str] | None = None,
    current_date: date | None = None,
    write: bool = False,
    queue_review: bool = False,
    approve_verification: bool = False,
    write_verification_plan: bool = False,
) -> SheetIntakeResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    effective_run_id = run_id or f"{today.isoformat()}_sheet-intake"
    action_set = {normalize_action(action) for action in (selected_actions or DEFAULT_SELECTED_ACTIONS)}
    normalized_rows = normalize_sheet_rows(rows)
    selected: list[SheetIntakeRow] = []
    skipped_count = 0
    findings: list[str] = []

    for row in normalized_rows:
        action = normalize_action(row.action)
        if action not in action_set:
            skipped_count += 1
            continue
        row_findings = validate_selected_row(repo_root, row, today)
        blocking_findings = [finding for finding in row_findings if finding.startswith("blocked:")]
        if blocking_findings:
            skipped_count += 1
            findings.extend(f"row {row.row_number}: {finding}" for finding in row_findings)
            continue
        findings.extend(f"row {row.row_number}: {finding}" for finding in row_findings)
        selected.append(row)

    leads = [sheet_row_to_candidate_lead(repo_root, row, today) for row in selected]
    written_paths: list[str] = []
    review_payload: dict[str, Any] | None = None
    verification_payload: dict[str, Any] | None = None
    review_ids: list[str] = []

    if write:
        market_dir = repo_root / "agents" / "runs" / effective_run_id / "market_research"
        market_dir.mkdir(parents=True, exist_ok=True)
        leads_path = market_dir / "sheet_intake_candidate_leads.json"
        report_path = market_dir / "sheet_intake.md"
        leads_path.write_text(json.dumps([asdict(lead) for lead in leads], indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report_path.write_text(
            format_sheet_intake_report(
                run_id=effective_run_id,
                generated_at=today,
                rows=selected,
                findings=findings,
                leads_path=leads_path.relative_to(repo_root).as_posix(),
            ),
            encoding="utf-8",
        )
        written_paths.extend([leads_path.relative_to(repo_root).as_posix(), report_path.relative_to(repo_root).as_posix()])

    if selected and not write and (queue_review or approve_verification or write_verification_plan):
        findings.append("queue/approval/verification-plan steps require write=True.")

    if selected and write:
        review = build_candidate_review(
            root=repo_root,
            run_id=effective_run_id,
            subject_id="",
            current_date=today,
            write=write,
            queue_review=queue_review,
        )
        review_payload = candidate_review_to_dict(review)
        written_paths.extend(path for path in review.written_paths if path not in written_paths)
        if queue_review:
            review_ids = candidate_review_ids(repo_root, effective_run_id)

    if approve_verification:
        if not queue_review or not write:
            findings.append("approve_verification requires write=True and queue_review=True.")
        elif review_ids:
            decision_result = apply_human_review_decisions(
                root=repo_root,
                decisions=[
                    HumanReviewDecision(
                        review_id=review_id,
                        status="approved",
                        note="Approved for verification from explicit sheet-intake request. This does not add the stock to monitoring.",
                        actor="user",
                    )
                    for review_id in review_ids
                ],
                current_date=today,
                write=True,
            )
            written_paths.extend(path for path in decision_result.written_paths if path not in written_paths)
            if decision_result.status == "blocked":
                findings.extend(f"approval blocked for {item.review_id}: {'; '.join(item.findings)}" for item in decision_result.items)

    if write_verification_plan:
        if not approve_verification:
            findings.append("write_verification_plan requires approve_verification=True.")
        elif write:
            followup = build_candidate_verification_followup(
                root=repo_root,
                run_id=effective_run_id,
                review_id="",
                current_date=today,
                write=True,
            )
            verification_payload = candidate_followup_to_dict(followup)
            written_paths.extend(path for path in followup.written_paths if path not in written_paths)

    status = sheet_intake_status(selected_count=len(selected), findings=findings, review_payload=review_payload, verification_payload=verification_payload)
    return SheetIntakeResult(
        run_id=effective_run_id,
        generated_at=today.isoformat(),
        status=status,
        selected_count=len(selected),
        skipped_count=skipped_count,
        review_ids=review_ids,
        findings=findings,
        written_paths=written_paths,
        candidate_review=review_payload,
        verification_followup=verification_payload,
    )


def normalize_sheet_rows(rows: list[dict[str, Any]] | list[list[Any]]) -> list[SheetIntakeRow]:
    if not rows:
        return []
    if all(isinstance(row, dict) for row in rows):
        return [normalize_sheet_row(row, fallback_row_number=index + 2) for index, row in enumerate(rows)]  # type: ignore[arg-type]
    if not all(isinstance(row, list) for row in rows):
        raise ValueError("Sheet rows must be a list of dicts or a list of row lists.")
    row_lists = rows  # type: ignore[assignment]
    if not row_lists:
        return []
    headers = [normalize_ascii(str(value)) for value in row_lists[0]]
    return [
        normalize_sheet_row(dict(zip(headers, row)), fallback_row_number=index + 2)
        for index, row in enumerate(row_lists[1:])
        if any(normalize_ascii(str(value)) for value in row)
    ]


def normalize_sheet_row(row: dict[str, Any], *, fallback_row_number: int) -> SheetIntakeRow:
    values = {normalize_header(key): normalize_ascii(str(value)) for key, value in row.items() if value is not None}
    row_number = parse_row_number(values.get("row_number", "") or values.get("__row_number", ""), fallback_row_number)
    return SheetIntakeRow(
        row_number=row_number,
        date_added=values.get("date", ""),
        name=values.get("name", ""),
        ticker=normalize_ticker(values.get("ticker", "")),
        industry=values.get("industry", ""),
        market_cap=values.get("mcap", ""),
        forward_pe=values.get("forward_pe", ""),
        price_to_sales=values.get("price_to_sales", ""),
        forecast=values.get("forecast", ""),
        score=values.get("score", "").upper(),
        available=normalize_option(values.get("available", "")),
        action=normalize_action(values.get("action", "")),
        comment=values.get("comment", ""),
        processing_status=normalize_option(values.get("processing_status", "") or values.get("workflow_status", "")),
        repo_link=values.get("repo_link", ""),
        last_checked=values.get("last_checked", ""),
    )


def sheet_row_to_candidate_lead(repo_root: Path, row: SheetIntakeRow, current_date: date) -> CandidateLead:
    cooldown_status = rejected_cooldown_status(repo_root, row.ticker, current_date)
    return CandidateLead(
        ticker=row.ticker,
        company_name=row.name,
        industry=row.industry,
        why_surfaced=why_surfaced(row),
        source_channels=["sheet"],
        source_ids=[f"sheet_row_{row.row_number}"],
        hype_level="unknown",
        sentiment="unknown",
        verification_status="unverified",
        strategy_fit="unknown",
        rejected_cooldown_status=cooldown_status,
        next_action="verify",
        rumor_flag=False,
        needs_human_review=True,
        notes=lead_notes(row),
    )


def validate_selected_row(repo_root: Path, row: SheetIntakeRow, current_date: date) -> list[str]:
    findings: list[str] = []
    if not row.ticker and not row.name:
        findings.append("blocked: selected row needs at least a ticker or company name.")
    if row.ticker and ticker_in_bucket(repo_root, "current_holdings", row.ticker):
        findings.append("blocked: ticker already exists in current holdings; update the sheet action to bought instead.")
    if row.ticker and ticker_in_bucket(repo_root, "monitoring", row.ticker):
        findings.append("blocked: ticker already exists in monitoring; update the sheet action to add to monitoring instead.")
    if normalize_option(row.available) == "no":
        findings.append("available=no; verification may still run, but promotion/buy decisions should stay blocked unless availability changes.")
    cooldown_status = rejected_cooldown_status(repo_root, row.ticker, current_date)
    if cooldown_status == "cooldown_active":
        findings.append("ticker is inside rejected cooldown; verification will route to cooldown override review.")
    if row.score and row.score not in SCORE_OPTIONS:
        findings.append(f"score '{row.score}' is outside the expected score dropdown.")
    return findings


def why_surfaced(row: SheetIntakeRow) -> str:
    parts = []
    label = row.name or row.ticker or f"sheet row {row.row_number}"
    parts.append(f"{label} was added through the quick stock-intake sheet.")
    if row.comment:
        parts.append(row.comment)
    if row.score:
        parts.append(f"User score: {row.score}.")
    if row.forecast:
        parts.append(f"Analyst forecast noted in sheet: {row.forecast}.")
    return " ".join(parts)


def lead_notes(row: SheetIntakeRow) -> str:
    notes = [
        f"sheet_row={row.row_number}",
        f"available={row.available or 'unknown'}",
        f"action={row.action or 'blank'}",
    ]
    if row.market_cap:
        notes.append(f"mcap={row.market_cap}")
    if row.forward_pe:
        notes.append(f"forward_pe={row.forward_pe}")
    if row.price_to_sales:
        notes.append(f"price_to_sales={row.price_to_sales}")
    return "; ".join(notes)


def candidate_review_ids(repo_root: Path, run_id: str) -> list[str]:
    queue_path = repo_root / "agents" / "human_review_queue.md"
    if not queue_path.exists():
        return []
    review_ids: list[str] = []
    prefix = f"agents/runs/{run_id}/market_research/candidate_review.md#"
    for line in queue_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| HRQ-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 8:
            continue
        if cells[7].startswith(prefix) and cells[5].lower() != "superseded":
            review_ids.append(cells[0])
    return review_ids


def rejected_cooldown_status(repo_root: Path, ticker: str, current_date: date) -> str:
    if not ticker:
        return "not_rejected"
    table = read_tracking_table(repo_root, "rejected")
    for row in table:
        if normalize_ticker(row.get("ticker", "")) != ticker:
            continue
        next_eligible = normalize_ascii(row.get("next_eligible_review_date", ""))
        if not next_eligible:
            return "rejected_missing_cooldown_date"
        try:
            if date.fromisoformat(next_eligible) > current_date:
                return "cooldown_active"
        except ValueError:
            return "rejected_missing_cooldown_date"
        return "not_rejected"
    return "not_rejected"


def ticker_in_bucket(repo_root: Path, bucket: str, ticker: str) -> bool:
    return any(normalize_ticker(row.get("ticker", "")) == normalize_ticker(ticker) for row in read_tracking_table(repo_root, bucket))


def read_tracking_table(repo_root: Path, bucket: str) -> list[dict[str, str]]:
    paths = {
        "current_holdings": repo_root / "stock_tracking" / "current_holdings" / "current_holdings.csv",
        "monitoring": repo_root / "stock_tracking" / "monitoring" / "monitoring.csv",
        "rejected": repo_root / "stock_tracking" / "rejected" / "rejected.csv",
    }
    path = paths[bucket]
    if not path.exists():
        return []
    return read_csv_table(path).rows


def format_sheet_intake_report(
    *,
    run_id: str,
    generated_at: date,
    rows: list[SheetIntakeRow],
    findings: list[str],
    leads_path: str,
) -> str:
    lines = [
        f"# Sheet Intake: {run_id}",
        "",
        f"Generated: {generated_at.isoformat()}",
        f"Source sheet: {SHEET_URL}",
        f"Tab: {SHEET_TAB}",
        "",
        "## Purpose",
        "",
        "This artifact captures rows that the user explicitly marked for research in the quick stock-intake sheet. It does not add stocks to monitoring, current holdings, or rejected state by itself.",
        "",
        "## Candidate Lead Artifact",
        "",
        f"- {leads_path}",
        "",
        "## Selected Rows",
        "",
        "| Sheet row | Ticker | Name | Score | Available | Action | Comment |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    if rows:
        for row in rows:
            lines.append(
                "| "
                + " | ".join(
                    escape_cell(value)
                    for value in [row.row_number, row.ticker, row.name, row.score, row.available, row.action, row.comment]
                )
                + " |"
            )
    else:
        lines.append("| none |  |  |  |  |  | No selected rows. |")
    lines.extend(["", "## Findings", ""])
    if findings:
        lines.extend(f"- {finding}" for finding in findings)
    else:
        lines.append("- None.")
    return "\n".join(lines).rstrip() + "\n"


def sheet_intake_status(
    *,
    selected_count: int,
    findings: list[str],
    review_payload: dict[str, Any] | None,
    verification_payload: dict[str, Any] | None,
) -> str:
    if selected_count == 0:
        return "no_selected_rows"
    if any("blocked:" in finding or "requires" in finding for finding in findings):
        return "partial"
    if verification_payload:
        return normalize_ascii(str(verification_payload.get("status", ""))) or "verification_planned"
    if review_payload:
        return normalize_ascii(str(review_payload.get("status", ""))) or "review_created"
    return "ready"


def load_rows_json(path: Path | str) -> list[dict[str, Any]] | list[list[Any]]:
    if str(path) == "-":
        data = json.loads(sys.stdin.read())
    else:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        rows = data.get("rows")
        headers = data.get("headers")
        if isinstance(rows, list) and isinstance(headers, list) and rows and all(isinstance(row, list) for row in rows):
            return [headers, *rows]
        if isinstance(rows, list):
            return rows
    if isinstance(data, list):
        return data
    raise ValueError("Rows JSON must be a list, or an object with a rows list.")


def result_to_dict(result: SheetIntakeResult) -> dict[str, Any]:
    return asdict(result)


def normalize_header(value: Any) -> str:
    key = normalize_ascii(str(value)).strip().lower()
    key = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
    aliases = {
        "date_added": "date",
        "company": "name",
        "company_name": "name",
        "market_cap": "mcap",
        "m_cap": "mcap",
        "forward_p_e": "forward_pe",
        "forward_pe": "forward_pe",
        "p_s": "price_to_sales",
        "ps": "price_to_sales",
        "price_sales": "price_to_sales",
        "price_to_sales": "price_to_sales",
        "price_to_sales_ttm": "price_to_sales",
        "source": "source_link",
        "source_url": "source_link",
        "link": "source_link",
        "source_link": "source_link",
        "repo_artifact": "repo_link",
        "repo_link": "repo_link",
        "processing_status": "processing_status",
        "codex_status": "processing_status",
        "workflow_status": "processing_status",
        "status": "processing_status",
        "row": "row_number",
        "row_number": "row_number",
    }
    return aliases.get(key, key)


def normalize_ticker(value: str) -> str:
    return normalize_ascii(value).strip().upper().lstrip("$").strip()


def normalize_action(value: str) -> str:
    action = normalize_option(value)
    aliases = {
        "": "capture",
        "save idea": "capture",
        "idea": "capture",
        "idea only": "capture",
        "new": "capture",
        "todo": "capture",
        "capture": "capture",
        "research": "research",
        "research next": "research",
        "review": "research",
        "run through research": "research",
        "do research": "research",
        "research_now": "research",
        "verify": "research",
        "validation": "research",
        "validate": "research",
        "run_research": "research",
        "run research": "research",
        "monitoring": "monitor",
        "monitor": "monitor",
        "add to monitoring": "monitor",
        "add_to_monitoring": "monitor",
        "watch": "monitor",
        "buy": "buy candidate",
        "buy candidate": "buy candidate",
        "consider_buying": "buy candidate",
        "consider buying": "buy candidate",
        "current_holding": "bought",
        "current holding": "bought",
        "owned": "bought",
        "bought": "bought",
        "skip": "ignore",
        "pass": "ignore",
        "ignore": "ignore",
        "rejected": "rejected",
    }
    return aliases.get(action, action)


def normalize_option(value: str) -> str:
    return re.sub(r"[_\s-]+", " ", normalize_ascii(value).strip().lower())


def parse_row_number(value: str, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed > 0 else fallback


def escape_cell(value: Any) -> str:
    return normalize_ascii(str(value)).replace("|", "/").replace("\n", " ").strip()
