from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from .agent_runtime.proposal_writer import resolve_target_path, update_last_updated
from .repo import find_repo_root, load_repo_state


@dataclass(frozen=True)
class FactualUpdateItem:
    update_id: str
    ticker: str
    target_file: str
    status: str
    areas: list[str]
    summary: str
    source_artifact: str
    findings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FactualUpdateResult:
    run_id: str
    generated_at: str
    status: str
    mode: str
    items: list[FactualUpdateItem]
    written_paths: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)


def build_company_file_factual_updates(
    *,
    root: Path | None = None,
    run_id: str,
    current_date: date | None = None,
    tickers: list[str] | None = None,
    write: bool = False,
    refresh: bool = False,
) -> FactualUpdateResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    selected = {ticker.upper() for ticker in tickers or [] if ticker.strip()}
    assessment_dir = repo_root / "agents" / "runs" / run_id / "raw" / "opportunity_assessment"
    items: list[FactualUpdateItem] = []
    findings: list[str] = []
    written_paths: list[str] = []

    if not assessment_dir.exists():
        return FactualUpdateResult(
            run_id=run_id,
            generated_at=today.isoformat(),
            status="blocked",
            mode="write" if write else "dry_run",
            items=[],
            findings=[f"Missing opportunity assessment directory: {assessment_dir}"],
        )

    for assessment_path in sorted(assessment_dir.glob("*_opportunity_assessment.json")):
        assessment = json.loads(assessment_path.read_text(encoding="utf-8"))
        ticker = str(assessment.get("ticker") or assessment_path.name.split("_", 1)[0]).upper()
        if selected and ticker not in selected:
            continue
        item = build_or_apply_one_factual_update(
            repo_root=repo_root,
            run_id=run_id,
            current_date=today,
            ticker=ticker,
            assessment=assessment,
            assessment_path=assessment_path,
            write=write,
            refresh=refresh,
        )
        items.append(item)

    if not items:
        findings.append("No matching opportunity assessment files found.")

    if write:
        summary_path = write_factual_update_summary(repo_root, run_id, today, items, findings)
        written_paths.append(relative_path(repo_root, summary_path))

    statuses = {item.status for item in items}
    if not items:
        status = "no_updates"
    elif statuses <= {"applied", "already_applied", "refreshed"}:
        status = "complete"
    elif statuses <= {"ready_to_apply", "already_applied"}:
        status = "ready_to_apply"
    elif "blocked" in statuses:
        status = "blocked"
    else:
        status = "partial"

    return FactualUpdateResult(
        run_id=run_id,
        generated_at=today.isoformat(),
        status=status,
        mode="write" if write else "dry_run",
        items=items,
        written_paths=written_paths,
        findings=findings,
    )


def build_or_apply_one_factual_update(
    *,
    repo_root: Path,
    run_id: str,
    current_date: date,
    ticker: str,
    assessment: dict[str, Any],
    assessment_path: Path,
    write: bool,
    refresh: bool,
) -> FactualUpdateItem:
    update_id = f"AUTOFACT-{run_id}-{ticker}"
    target_file, target_findings = find_company_file_for_ticker(repo_root, ticker)
    source_artifact = source_report_path(repo_root, run_id, ticker, fallback=assessment_path)
    quality_findings = [str(item) for item in assessment.get("quality_findings", []) if str(item).strip()]
    findings = [*target_findings]
    if quality_findings:
        findings.append("Opportunity assessment has quality findings; factual update requires manual review.")
    if not target_file:
        return FactualUpdateItem(
            update_id=update_id,
            ticker=ticker,
            target_file="",
            status="blocked",
            areas=[],
            summary="No stock info file found for ticker.",
            source_artifact=relative_path(repo_root, source_artifact),
            findings=findings,
        )

    target_rel = relative_path(repo_root, target_file)
    resolved_target, target_errors = resolve_target_path(repo_root, target_rel)
    if target_errors:
        findings.extend(target_errors)
        return FactualUpdateItem(
            update_id=update_id,
            ticker=ticker,
            target_file=target_rel,
            status="blocked",
            areas=[],
            summary="Target file failed safety validation.",
            source_artifact=relative_path(repo_root, source_artifact),
            findings=findings,
        )

    if quality_findings:
        return FactualUpdateItem(
            update_id=update_id,
            ticker=ticker,
            target_file=target_rel,
            status="blocked",
            areas=[],
            summary="Blocked because the source assessment has unresolved quality findings.",
            source_artifact=relative_path(repo_root, source_artifact),
            findings=findings,
        )

    current_text = resolved_target.read_text(encoding="utf-8")
    if update_id in current_text and not refresh:
        return FactualUpdateItem(
            update_id=update_id,
            ticker=ticker,
            target_file=target_rel,
            status="already_applied",
            areas=["idempotency"],
            summary="This factual update was already applied.",
            source_artifact=relative_path(repo_root, source_artifact),
            findings=findings,
        )

    rows = build_factual_rows(update_id, ticker, run_id, current_date, assessment, repo_root, source_artifact)
    if not rows:
        return FactualUpdateItem(
            update_id=update_id,
            ticker=ticker,
            target_file=target_rel,
            status="blocked",
            areas=[],
            summary="No low-risk factual rows could be extracted from the assessment.",
            source_artifact=relative_path(repo_root, source_artifact),
            findings=findings,
        )

    if write:
        new_text = remove_existing_update_rows(current_text, update_id) if refresh else current_text
        new_text = update_last_updated(new_text, current_date)
        new_text = ensure_section_table(
            new_text,
            "Automated Factual Updates",
            ["Date", "Update ID", "Area", "Summary", "Source"],
        )
        for row in rows:
            new_text = append_row_to_section_table(new_text, "Automated Factual Updates", row)
        new_text = ensure_source_log_entry(new_text, current_date, update_id, source_artifact, repo_root)
        new_text = ensure_change_log_entry(new_text, current_date, update_id, source_artifact, repo_root)
        resolved_target.write_text(new_text, encoding="utf-8")

    return FactualUpdateItem(
        update_id=update_id,
        ticker=ticker,
        target_file=target_rel,
        status="refreshed" if write and update_id in current_text and refresh else ("applied" if write else "ready_to_apply"),
        areas=[row[2] for row in rows],
        summary=rows[0][3],
        source_artifact=relative_path(repo_root, source_artifact),
        findings=findings,
    )


def find_company_file_for_ticker(repo_root: Path, ticker: str) -> tuple[Path | None, list[str]]:
    state = load_repo_state(repo_root)
    findings: list[str] = []
    for table_name in ("current_holdings", "monitoring"):
        table = state.stock_tables.get(table_name)
        if not table:
            continue
        for row in table.rows:
            if str(row.get("ticker", "")).upper() != ticker.upper():
                continue
            target = str(row.get("stock_info_file", "")).strip()
            if target:
                return repo_root / target, findings
            findings.append(f"{ticker} exists in {table_name}, but stock_info_file is blank.")
    return None, [f"{ticker} is not present in current holdings or monitoring CSVs."]


def build_factual_rows(
    update_id: str,
    ticker: str,
    run_id: str,
    current_date: date,
    assessment: dict[str, Any],
    repo_root: Path,
    source_artifact: Path,
) -> list[list[str]]:
    source_link = markdown_file_link(relative_path(repo_root, source_artifact))
    rows: list[list[str]] = []
    summary = format_assessment_summary(assessment)
    if summary:
        rows.append([current_date.isoformat(), update_id, "assessment_summary", summary, source_link])

    financial = assessment.get("financial_snapshot") or {}
    financial_summary = format_financial_snapshot(financial)
    if financial_summary:
        rows.append([current_date.isoformat(), update_id, "financial_snapshot", financial_summary, source_link])

    news = assessment.get("news_snapshot") or {}
    developments = summarize_list(
        news.get("material_developments") or news.get("material_claims") or news.get("contents_claims") or [],
        limit=3,
    )
    if developments:
        rows.append([current_date.isoformat(), update_id, "developments", developments, source_link])

    social = assessment.get("social_snapshot") or {}
    social_summary = format_social_snapshot(social)
    if social_summary:
        rows.append([current_date.isoformat(), update_id, "grok_x_social_signal", social_summary, source_link])

    watch_items = summarize_list(assessment.get("watch_items") or [], limit=3)
    if watch_items:
        rows.append([current_date.isoformat(), update_id, "watch_items", watch_items, source_link])

    return rows


def format_financial_snapshot(financial: dict[str, Any]) -> str:
    parts = []
    warnings = [str(item).strip() for item in financial.get("valuation_sanity_warnings", []) if str(item).strip()]
    if warnings:
        parts.append("valuation needs verification before using headline price/market cap/P/E")
    for label, key in [
        ("price", "latest_price"),
        ("market cap", "market_cap"),
        ("P/E", "pe_ratio"),
        ("forward P/E", "forward_pe"),
        ("revenue growth YoY", "quarterly_revenue_growth_yoy"),
        ("operating margin", "operating_margin_ttm"),
        ("analyst target", "analyst_target_price"),
        ("target upside", "analyst_target_implied_upside"),
    ]:
        value = financial.get(key)
        if value in ("", None):
            continue
        parts.append(f"{label}: {format_value(value, percent=key in PERCENT_FIELDS)}")
    for warning in warnings[:2]:
        parts.append(f"sanity warning: {clean_cell(warning)}")
    return "; ".join(parts)


def format_social_snapshot(social: dict[str, Any]) -> str:
    parts = []
    sentiment = clean_cell(str(social.get("sentiment") or ""))
    if sentiment:
        parts.append(f"Sentiment: {sentiment}")
    pulse = clean_cell(str(social.get("x_pulse") or social.get("summary_excerpt") or ""))
    if pulse:
        parts.append(f"Pulse: {pulse}")
    bullish = summarize_list(social.get("bullish_claims") or [], limit=2)
    bearish = summarize_list(social.get("bearish_claims") or [], limit=2)
    if bullish:
        parts.append(f"Bullish: {bullish}")
    if bearish:
        parts.append(f"Bearish: {bearish}")
    return " | ".join(parts)


PERCENT_FIELDS = {
    "quarterly_revenue_growth_yoy",
    "operating_margin_ttm",
    "analyst_target_implied_upside",
}


def format_assessment_summary(assessment: dict[str, Any]) -> str:
    parts = []
    score = assessment.get("opportunity_score")
    view = assessment.get("opportunity_view")
    risk = assessment.get("risk_level")
    confidence = assessment.get("confidence")
    if score not in ("", None):
        parts.append(f"Opportunity score {score}/100")
    if view:
        parts.append(f"view: {view}")
    if risk:
        parts.append(f"risk: {risk}")
    if confidence:
        parts.append(f"confidence: {confidence}")
    next_action = clean_cell(str(assessment.get("recommended_next_action") or ""))
    if next_action:
        parts.append(f"next check: {next_action}")
    return "; ".join(parts)


def ensure_source_log_entry(text: str, current_date: date, update_id: str, source_artifact: Path, repo_root: Path) -> str:
    text = ensure_section_table(text, "Source Log", ["Date", "Source", "Type", "Relevance", "Link / Location"])
    row = [
        current_date.isoformat(),
        update_id,
        "internal artifact",
        "Low-risk factual sync from opportunity assessment; no thesis/status/trade decision changed.",
        markdown_file_link(relative_path(repo_root, source_artifact)),
    ]
    return append_row_to_section_table(text, "Source Log", row)


def ensure_change_log_entry(text: str, current_date: date, update_id: str, source_artifact: Path, repo_root: Path) -> str:
    text = ensure_section_table(text, "Change Log", ["Date", "Updated by", "Change", "Reason / Source"])
    row = [
        current_date.isoformat(),
        "Codex factual update writer",
        f"Applied {update_id}: synced factual assessment, financial, news, social, and watch-item summaries.",
        markdown_file_link(relative_path(repo_root, source_artifact)),
    ]
    return append_row_to_section_table(text, "Change Log", row)


def ensure_section_table(text: str, heading: str, headers: list[str]) -> str:
    heading_line = f"## {heading}"
    table_header = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    if heading_line not in text:
        return text.rstrip() + f"\n\n{heading_line}\n\n{table_header}\n{separator}\n"
    section_start = text.index(heading_line)
    next_section = text.find("\n## ", section_start + len(heading_line))
    section = text[section_start:] if next_section == -1 else text[section_start:next_section]
    if table_header in section:
        return text
    insert_at = section_start + len(heading_line)
    return text[:insert_at] + f"\n\n{table_header}\n{separator}\n" + text[insert_at:]


def append_row_to_section_table(text: str, heading: str, row: list[str]) -> str:
    heading_line = f"## {heading}"
    section_start = text.index(heading_line)
    next_section = text.find("\n## ", section_start + len(heading_line))
    section_end = len(text) if next_section == -1 else next_section
    row_line = "| " + " | ".join(clean_cell(cell) for cell in row) + " |"
    section = text[section_start:section_end]
    if row_line in section:
        return text
    insertion = "\n" + row_line
    return text[:section_end].rstrip() + insertion + "\n\n" + text[section_end:].lstrip("\n")


def write_factual_update_summary(
    repo_root: Path,
    run_id: str,
    current_date: date,
    items: list[FactualUpdateItem],
    findings: list[str],
) -> Path:
    path = repo_root / "agents" / "runs" / run_id / "company_file_factual_updates.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Company File Factual Updates: {run_id}",
        "",
        f"Generated: {current_date.isoformat()}",
        "",
        "This is an FYI summary of low-risk factual updates. It does not record thesis, status, buy/sell, or strategy changes.",
        "",
        "| Ticker | Status | Target File | Areas | Summary | Source |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    if items:
        for item in items:
            lines.append(
                "| "
                + " | ".join(
                    clean_cell(value)
                    for value in [
                        item.ticker,
                        item.status,
                        markdown_file_link(item.target_file) if item.target_file else "",
                        ", ".join(item.areas),
                        item.summary,
                        markdown_file_link(item.source_artifact),
                    ]
                )
                + " |"
            )
    else:
        lines.append("|  | no_updates |  |  | No factual updates found. |  |")
    if findings:
        lines.extend(["", "## Findings", ""])
        lines.extend(f"- {finding}" for finding in findings)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def source_report_path(repo_root: Path, run_id: str, ticker: str, fallback: Path) -> Path:
    report = repo_root / "agents" / "runs" / run_id / "reports" / "opportunity_assessment" / f"{ticker}_opportunity_assessment.md"
    return report if report.exists() else fallback


def summarize_list(values: list[Any], limit: int) -> str:
    cleaned = [clean_cell(extract_item_text(value)) for value in values if clean_cell(extract_item_text(value))]
    return " / ".join(cleaned[:limit])


def extract_item_text(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("claim", "summary", "title", "development", "text", "name"):
            if value.get(key):
                return str(value[key])
        return "; ".join(f"{key}: {item}" for key, item in value.items() if item not in ("", None))
    return str(value)


def format_value(value: Any, *, percent: bool = False) -> str:
    if isinstance(value, float):
        if percent:
            return f"{value * 100:.1f}%"
        if abs(value) >= 1_000_000_000:
            return f"{value / 1_000_000_000:.1f}B"
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        return f"{value:.2f}"
    if percent and isinstance(value, int):
        return f"{value * 100:.1f}%"
    return str(value)


def remove_existing_update_rows(text: str, update_id: str) -> str:
    lines = [line for line in text.splitlines() if update_id not in line]
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def clean_cell(value: str) -> str:
    value = re.sub(r"\[\[\d+\]\]\([^)]+\)", "", value)
    value = re.sub(r"(?<!\w)\[(\d+)\](?!\()", "", value)
    return " ".join(value.replace("|", "/").split())


def markdown_file_link(path: str) -> str:
    return f"[{path}]({path})"


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def factual_update_result_to_dict(result: FactualUpdateResult) -> dict[str, Any]:
    return asdict(result)
