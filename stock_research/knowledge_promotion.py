from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from .repo import RepoState, find_repo_root, load_repo_state


REQUIRED_MARKDOWN_ARTIFACTS = (
    "run_summary.md",
    "quality_report.md",
    "memory_reflection.md",
    "finalization.md",
)

TICKER_ARTIFACT_PATTERNS = (
    ("reports/human_synthesis/*_synthesis_pack.md", "_synthesis_pack"),
    ("reports/human_synthesis/*_final_human_report.md", "_final_human_report"),
    ("reports/opportunity_assessment/*_opportunity_assessment.md", "_opportunity_assessment"),
    ("reports/company_news_specialist/*_company_news_review.md", "_company_news_review"),
    ("reports/financial_data_specialist/*_financial_review.md", "_financial_review"),
    ("company_research/*_company_research.md", "_company_research"),
    ("raw/opportunity_assessment/*_opportunity_assessment.json", "_opportunity_assessment"),
)

RESOLVED_REVIEW_STATUSES = {"done", "closed", "resolved", "rejected", "superseded", "applied"}


@dataclass(frozen=True)
class KnowledgePromotionFinding:
    area: str
    status: str
    summary: str
    evidence: list[str] = field(default_factory=list)
    next_action: str = ""


@dataclass(frozen=True)
class KnowledgePromotionResult:
    run_id: str
    generated_at: str
    status: str
    cleanup_ready: bool
    blocker_count: int
    waiting_count: int
    warning_count: int
    durable_surfaces: list[str]
    findings: list[KnowledgePromotionFinding]
    written_paths: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class StockTarget:
    ticker: str
    category: str
    stock_info_file: str


def assess_knowledge_promotion(
    *,
    root: Path | None = None,
    run_id: str,
    current_date: date | None = None,
    write: bool = False,
) -> KnowledgePromotionResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    run_dir = repo_root / "agents" / "runs" / run_id
    state = load_repo_state(repo_root)
    findings: list[KnowledgePromotionFinding] = []

    if not run_dir.exists():
        findings.append(
            KnowledgePromotionFinding(
                area="run",
                status="blocked",
                summary="Run directory does not exist.",
                evidence=[relative_path(repo_root, run_dir)],
                next_action="Use an existing run id before assessing promotion status.",
            )
        )
        return finalize_result(repo_root, run_dir, run_id, today, findings, [], write)

    run_tickers = extract_run_tickers(run_dir)
    stock_targets = stock_targets_by_ticker(state)
    review_refs = review_items_for_run(state, run_id)

    findings.append(check_required_artifacts(repo_root, run_dir))
    findings.append(check_final_human_reports(repo_root, run_dir))
    findings.extend(check_company_promotions(repo_root, run_dir, run_id, run_tickers, stock_targets))
    findings.extend(check_category_state_promotions(repo_root, run_id, run_tickers, stock_targets, state))
    findings.append(check_memory_drafts(repo_root, run_dir))
    findings.append(check_human_review_refs(review_refs))
    market_finding = check_market_research_promotion(repo_root, run_dir, run_id, review_refs)
    if market_finding:
        findings.append(market_finding)
    findings.append(check_archive_index(repo_root, run_id))

    durable_surfaces = durable_surfaces_for_run(repo_root, run_id, run_tickers, stock_targets)
    return finalize_result(repo_root, run_dir, run_id, today, findings, durable_surfaces, write)


def finalize_result(
    repo_root: Path,
    run_dir: Path,
    run_id: str,
    current_date: date,
    findings: list[KnowledgePromotionFinding],
    durable_surfaces: list[str],
    write: bool,
) -> KnowledgePromotionResult:
    blocker_count = len([finding for finding in findings if finding.status == "blocked"])
    waiting_count = len([finding for finding in findings if finding.status == "waiting"])
    warning_count = len([finding for finding in findings if finding.status == "warning"])
    cleanup_ready = blocker_count == 0 and waiting_count == 0
    if blocker_count:
        status = "blocked"
    elif waiting_count:
        status = "waiting_for_human_review"
    else:
        status = "promoted"

    result = KnowledgePromotionResult(
        run_id=run_id,
        generated_at=current_date.isoformat(),
        status=status,
        cleanup_ready=cleanup_ready,
        blocker_count=blocker_count,
        waiting_count=waiting_count,
        warning_count=warning_count,
        durable_surfaces=dedupe_strings(durable_surfaces),
        findings=findings,
    )
    if not write:
        return result

    written_paths = write_knowledge_promotion_status(repo_root, run_dir, result)
    return KnowledgePromotionResult(
        run_id=result.run_id,
        generated_at=result.generated_at,
        status=result.status,
        cleanup_ready=result.cleanup_ready,
        blocker_count=result.blocker_count,
        waiting_count=result.waiting_count,
        warning_count=result.warning_count,
        durable_surfaces=result.durable_surfaces,
        findings=result.findings,
        written_paths=written_paths,
    )


def check_required_artifacts(repo_root: Path, run_dir: Path) -> KnowledgePromotionFinding:
    run_id = run_dir.name
    missing = [
        relative_path(repo_root, run_dir / name)
        for name in REQUIRED_MARKDOWN_ARTIFACTS
        if not run_or_archived_artifact(repo_root, run_id, name).exists()
    ]
    if missing:
        return KnowledgePromotionFinding(
            area="run_artifacts",
            status="blocked",
            summary="Required run summary, quality, memory reflection, or finalization markdown is missing.",
            evidence=missing,
            next_action="Regenerate run summary, quality report, memory reflection, and finalization before cleanup.",
        )
    return KnowledgePromotionFinding(
        area="run_artifacts",
        status="passed",
        summary="Required markdown and finalization artifacts exist.",
        evidence=[relative_path(repo_root, run_or_archived_artifact(repo_root, run_id, name)) for name in REQUIRED_MARKDOWN_ARTIFACTS],
    )


def check_final_human_reports(repo_root: Path, run_dir: Path) -> KnowledgePromotionFinding:
    synthesis_dir = run_dir / "reports" / "human_synthesis"
    if not synthesis_dir.exists():
        return KnowledgePromotionFinding(
            area="final_reports",
            status="passed",
            summary="No human synthesis packs were found, so no final human reports are required.",
        )
    missing: list[str] = []
    packs = sorted(synthesis_dir.glob("*_synthesis_pack.md"))
    for pack in packs:
        ticker = pack.name.replace("_synthesis_pack.md", "")
        final_report = pack.with_name(f"{ticker}_final_human_report.md")
        final_rel = final_report.relative_to(run_dir).as_posix()
        if not run_or_archived_artifact(repo_root, run_dir.name, final_rel).exists():
            missing.append(relative_path(repo_root, final_report))
    if missing:
        return KnowledgePromotionFinding(
            area="final_reports",
            status="blocked",
            summary="One or more human synthesis packs do not have canonical final human reports.",
            evidence=missing,
            next_action="Write or regenerate each missing *_final_human_report.md, then rerun the promotion check.",
        )
    return KnowledgePromotionFinding(
        area="final_reports",
        status="passed",
        summary=f"All {len(packs)} human synthesis pack(s) have canonical final human reports.",
        evidence=[relative_path(repo_root, path) for path in packs],
    )


def check_company_promotions(
    repo_root: Path,
    run_dir: Path,
    run_id: str,
    run_tickers: list[str],
    stock_targets: dict[str, StockTarget],
) -> list[KnowledgePromotionFinding]:
    findings: list[KnowledgePromotionFinding] = []
    if not run_tickers:
        return [
            KnowledgePromotionFinding(
                area="company_files",
                status="passed",
                summary="No ticker-specific research artifacts were found for this run.",
            )
        ]

    for ticker in run_tickers:
        target = stock_targets.get(ticker)
        if not target:
            findings.append(
                KnowledgePromotionFinding(
                    area="company_files",
                    status="warning",
                    summary=f"{ticker} is not in current holdings, monitoring, or rejected CSVs.",
                    evidence=[relative_path(repo_root, path) for path in ticker_artifacts_for_run(run_dir, ticker)],
                    next_action="If this ticker should remain useful, route it to monitoring, rejected, market research, or a human-review decision.",
                )
            )
            continue
        if target.category == "rejected":
            findings.append(
                KnowledgePromotionFinding(
                    area="company_files",
                    status="warning",
                    summary=f"{ticker} is in rejected tracking; rejected cooldown/reason should be the durable surface, not active company research.",
                    evidence=[target.stock_info_file or "stock_tracking/rejected/rejected.csv"],
                    next_action="Confirm the rejected row or rejected company file links the run conclusion before archiving markdown.",
                )
            )
            continue
        if not target.stock_info_file:
            findings.append(
                KnowledgePromotionFinding(
                    area="company_files",
                    status="blocked",
                    summary=f"{ticker} is active but has no stock_info_file path in its CSV row.",
                    evidence=[f"stock_tracking/{target.category}/{target.category}.csv"],
                    next_action="Add the company file path to the CSV row and rerun promotion.",
                )
            )
            continue
        company_file = repo_root / target.stock_info_file
        if not company_file.exists():
            findings.append(
                KnowledgePromotionFinding(
                    area="company_files",
                    status="blocked",
                    summary=f"{ticker} is active but its company file is missing.",
                    evidence=[target.stock_info_file],
                    next_action="Create or restore the company file before cleaning run artifacts.",
                )
            )
            continue
        text = company_file.read_text(encoding="utf-8")
        expected_markers = [f"AUTOFACT-{run_id}-{ticker}", f"PROMOTED-{run_id}-{ticker}"]
        if any(marker in text for marker in expected_markers):
            findings.append(
                KnowledgePromotionFinding(
                    area="company_files",
                    status="passed",
                    summary=f"{ticker} has a deterministic promotion marker in its active company file.",
                    evidence=[target.stock_info_file],
                )
            )
            continue
        findings.append(
            KnowledgePromotionFinding(
                area="company_files",
                status="blocked",
                summary=f"{ticker} lacks a deterministic company-file promotion marker for this run.",
                evidence=[target.stock_info_file, *[relative_path(repo_root, path) for path in ticker_artifacts_for_run(run_dir, ticker)]],
                next_action=(
                    f"Run the scoped factual updater or add a reviewed PROMOTED-{run_id}-{ticker} row with source-backed "
                    "summary in the company file before JSON cleanup."
                ),
            )
        )
    return findings


def check_category_state_promotions(
    repo_root: Path,
    run_id: str,
    run_tickers: list[str],
    stock_targets: dict[str, StockTarget],
    state: RepoState,
) -> list[KnowledgePromotionFinding]:
    active_categories = sorted(
        {
            target.category
            for ticker, target in stock_targets.items()
            if ticker in set(run_tickers) and target.category in {"current_holdings", "monitoring"}
        }
    )
    if not active_categories:
        return [
            KnowledgePromotionFinding(
                area="category_state",
                status="passed",
                summary="No active holding or monitoring ticker from this run requires a category-state marker.",
            )
        ]
    findings: list[KnowledgePromotionFinding] = []
    marker = f"CATSTATE-{run_id}"
    for category in active_categories:
        path = state.category_state_files[category]
        rel = relative_path(repo_root, path)
        if not path.exists():
            findings.append(
                KnowledgePromotionFinding(
                    area="category_state",
                    status="blocked",
                    summary=f"Missing {category} state file.",
                    evidence=[rel],
                    next_action="Restore the category state file, then run category-state update.",
                )
            )
            continue
        text = path.read_text(encoding="utf-8")
        if marker in text:
            findings.append(
                KnowledgePromotionFinding(
                    area="category_state",
                    status="passed",
                    summary=f"{category} state includes the run-level automated state marker.",
                    evidence=[rel],
                )
            )
        else:
            findings.append(
                KnowledgePromotionFinding(
                    area="category_state",
                    status="blocked",
                    summary=f"{category} state lacks CATSTATE marker for this run.",
                    evidence=[rel],
                    next_action="Run category-state update for this run after company-file promotion is complete.",
                )
            )
    return findings


def check_memory_drafts(repo_root: Path, run_dir: Path) -> KnowledgePromotionFinding:
    json_path = run_dir / "memory_update_drafts.json"
    md_path = run_dir / "memory_update_drafts.md"
    missing = [relative_path(repo_root, path) for path in (json_path, md_path) if not path.exists()]
    if missing:
        return KnowledgePromotionFinding(
            area="operational_memory",
            status="blocked",
            summary="Memory update draft artifacts are missing, so operational lessons were not reviewably handled.",
            evidence=missing,
            next_action="Run memory draft-updates/writer-review, then apply, reject, or block each draft explicitly.",
        )
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return KnowledgePromotionFinding(
            area="operational_memory",
            status="blocked",
            summary="memory_update_drafts.json is invalid JSON.",
            evidence=[relative_path(repo_root, json_path)],
            next_action="Regenerate memory update drafts before cleanup.",
        )
    items = list(data.get("items", []))
    ready = [str(item.get("proposal_id", "ready_memory_update")) for item in items if str(item.get("status", "")).lower() == "ready"]
    if ready:
        return KnowledgePromotionFinding(
            area="operational_memory",
            status="blocked",
            summary="Ready memory-update drafts still need an explicit apply/reject/supersede decision.",
            evidence=ready,
            next_action="Apply approved ready drafts with memory apply-updates or mark them rejected/superseded through writer review.",
        )
    blocked_or_rejected = [
        str(item.get("proposal_id", "memory_update"))
        for item in items
        if str(item.get("status", "")).lower() in {"blocked", "rejected"}
    ]
    if blocked_or_rejected:
        return KnowledgePromotionFinding(
            area="operational_memory",
            status="warning",
            summary="No ready memory drafts remain, but some proposed lessons were blocked or rejected.",
            evidence=blocked_or_rejected,
            next_action="Review blocked/rejected draft reasons if the run exposed a major operational lesson.",
        )
    applied = [str(item.get("proposal_id", "memory_update")) for item in items if str(item.get("status", "")).lower() == "applied"]
    return KnowledgePromotionFinding(
        area="operational_memory",
        status="passed",
        summary=f"Operational memory drafts are handled ({len(applied)} applied, {len(items)} total).",
        evidence=[relative_path(repo_root, md_path)],
    )


def check_human_review_refs(review_refs: list[dict[str, str]]) -> KnowledgePromotionFinding:
    if not review_refs:
        return KnowledgePromotionFinding(
            area="human_review",
            status="passed",
            summary="No human-review queue rows reference this run.",
        )
    pending = [item for item in review_refs if not review_status_resolved(item)]
    if pending:
        return KnowledgePromotionFinding(
            area="human_review",
            status="waiting",
            summary="Human-review rows still reference this run and need a final decision or completed follow-up.",
            evidence=[review_item_label(item) for item in pending],
            next_action="Resolve, complete, reject, or supersede the referenced HRQ rows before cleaning run JSON.",
        )
    return KnowledgePromotionFinding(
        area="human_review",
        status="passed",
        summary="Human-review rows that reference this run are resolved.",
        evidence=[review_item_label(item) for item in review_refs],
    )


def check_market_research_promotion(
    repo_root: Path,
    run_dir: Path,
    run_id: str,
    review_refs: list[dict[str, str]],
) -> KnowledgePromotionFinding | None:
    market_artifacts = sorted(run_dir.glob("market_research/*.md"))
    if not market_artifacts:
        return None

    rel_artifacts = [relative_path(repo_root, path) for path in market_artifacts]
    if review_refs:
        pending = [item for item in review_refs if not review_status_resolved(item)]
        if pending:
            return KnowledgePromotionFinding(
                area="market_research",
                status="waiting",
                summary="Market-research artifacts are linked to pending human-review rows.",
                evidence=rel_artifacts,
                next_action="Complete or supersede the linked market-research review decisions before cleanup.",
            )
        return KnowledgePromotionFinding(
            area="market_research",
            status="passed",
            summary="Market-research artifacts are linked through resolved human-review rows.",
            evidence=rel_artifacts,
        )

    durable_refs = durable_market_references(repo_root, run_id)
    if durable_refs:
        return KnowledgePromotionFinding(
            area="market_research",
            status="passed",
            summary="Market-research run is referenced from durable market, strategy, or request files.",
            evidence=durable_refs,
        )
    return KnowledgePromotionFinding(
        area="market_research",
        status="blocked",
        summary="Market-research artifacts exist but are not linked from HRQ, market research, strategy, or request files.",
        evidence=rel_artifacts,
        next_action="Queue a human-review decision or add a concise durable market/strategy/request reference before cleanup.",
    )


def check_archive_index(repo_root: Path, run_id: str) -> KnowledgePromotionFinding:
    index_path = repo_root / "archive" / "research_index.md"
    if index_path.exists() and run_id in index_path.read_text(encoding="utf-8"):
        return KnowledgePromotionFinding(
            area="archive_index",
            status="passed",
            summary="Archive research index references this run.",
            evidence=[relative_path(repo_root, index_path)],
        )
    return KnowledgePromotionFinding(
        area="archive_index",
        status="warning",
        summary="Archive research index does not yet reference this run.",
        evidence=[relative_path(repo_root, index_path)],
        next_action="Run artifact-hygiene inventory --write so markdown artifacts remain findable after they leave the active run tree.",
    )


def extract_run_tickers(run_dir: Path) -> list[str]:
    tickers: list[str] = []
    for pattern, suffix in TICKER_ARTIFACT_PATTERNS:
        for path in sorted(run_dir.glob(pattern)):
            ticker = strip_suffix(path.stem, suffix).upper()
            if is_likely_ticker(ticker) and ticker not in tickers:
                tickers.append(ticker)
    return tickers


def ticker_artifacts_for_run(run_dir: Path, ticker: str) -> list[Path]:
    result: list[Path] = []
    ticker_upper = ticker.upper()
    for pattern, suffix in TICKER_ARTIFACT_PATTERNS:
        for path in sorted(run_dir.glob(pattern)):
            if strip_suffix(path.stem, suffix).upper() == ticker_upper:
                result.append(path)
    return result


def stock_targets_by_ticker(state: RepoState) -> dict[str, StockTarget]:
    result: dict[str, StockTarget] = {}
    for category, table in state.stock_tables.items():
        for row in table.rows:
            ticker = str(row.get("ticker", "")).strip().upper()
            if not ticker:
                continue
            result[ticker] = StockTarget(
                ticker=ticker,
                category=category,
                stock_info_file=str(row.get("stock_info_file", "")).strip(),
            )
    return result


def review_items_for_run(state: RepoState, run_id: str) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for item in state.human_review_items:
        if any(run_id in str(value) for value in item.values()):
            result.append(item)
    return result


def review_status_resolved(item: dict[str, str]) -> bool:
    status = str(item.get("Status", "") or item.get("status", "")).strip().lower()
    return status in RESOLVED_REVIEW_STATUSES


def review_item_label(item: dict[str, str]) -> str:
    review_id = str(item.get("ID", "") or item.get("id", "")).strip() or "HRQ"
    status = str(item.get("Status", "") or item.get("status", "")).strip() or "unknown"
    decision = str(item.get("Decision Needed", "") or item.get("decision_needed", "") or item.get("Type", "") or "").strip()
    return clean_cell(f"{review_id} ({status}) {decision}")


def durable_market_references(repo_root: Path, run_id: str) -> list[str]:
    roots = [
        repo_root / "market_research",
        repo_root / "strategy",
        repo_root / "docs" / "plans",
    ]
    refs: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.md")):
            if path.parts[-2:] == ("agents", "runs"):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if run_id in text:
                refs.append(relative_path(repo_root, path))
    return dedupe_strings(refs)


def durable_surfaces_for_run(
    repo_root: Path,
    run_id: str,
    run_tickers: list[str],
    stock_targets: dict[str, StockTarget],
) -> list[str]:
    surfaces = [
        relative_path(repo_root, run_or_archived_artifact(repo_root, run_id, "run_summary.md")),
        relative_path(repo_root, run_or_archived_artifact(repo_root, run_id, "quality_report.md")),
        relative_path(repo_root, run_or_archived_artifact(repo_root, run_id, "memory_reflection.md")),
        relative_path(repo_root, run_or_archived_artifact(repo_root, run_id, "finalization.md")),
        f"agents/runs/{run_id}/memory_update_drafts.md",
    ]
    for ticker in run_tickers:
        target = stock_targets.get(ticker)
        if target and target.stock_info_file:
            surfaces.append(target.stock_info_file)
    for category in sorted({stock_targets[ticker].category for ticker in run_tickers if ticker in stock_targets}):
        if category in {"current_holdings", "monitoring", "rejected"}:
            surfaces.append(f"stock_tracking/{category}/{category}_state.md")
    if (repo_root / "agents" / "human_review_queue.md").exists():
        surfaces.append("agents/human_review_queue.md")
    if (repo_root / "archive" / "research_index.md").exists():
        surfaces.append("archive/research_index.md")
    return dedupe_strings(surfaces)


def write_knowledge_promotion_status(repo_root: Path, run_dir: Path, result: KnowledgePromotionResult) -> list[str]:
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "knowledge_promotion_status.json"
    md_path = run_dir / "knowledge_promotion_status.md"
    json_path.write_text(json.dumps(knowledge_promotion_result_to_dict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_knowledge_promotion_markdown(result), encoding="utf-8")
    return [relative_path(repo_root, json_path), relative_path(repo_root, md_path)]


def run_or_archived_artifact(repo_root: Path, run_id: str, rel_inside_run: str) -> Path:
    active = repo_root / "agents" / "runs" / run_id / rel_inside_run
    if active.exists():
        return active
    year = run_id[:4] if run_id[:4].isdigit() else "unknown"
    archived = repo_root / "archive" / "runs" / year / run_id / rel_inside_run
    return archived if archived.exists() else active


def format_knowledge_promotion_markdown(result: KnowledgePromotionResult) -> str:
    lines = [
        f"# Knowledge Promotion Status: {result.run_id}",
        "",
        f"Generated: {result.generated_at}",
        f"Status: {result.status}",
        f"Cleanup ready: {'yes' if result.cleanup_ready else 'no'}",
        f"Blockers: {result.blocker_count}",
        f"Waiting: {result.waiting_count}",
        f"Warnings: {result.warning_count}",
        "",
        "## Findings",
        "",
        "| Area | Status | Summary | Evidence | Next Action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for finding in result.findings:
        lines.append(
            "| "
            + " | ".join(
                clean_cell(value)
                for value in [
                    finding.area,
                    finding.status,
                    finding.summary,
                    "; ".join(finding.evidence),
                    finding.next_action,
                ]
            )
            + " |"
        )
    lines.extend(["", "## Durable Surfaces", ""])
    if result.durable_surfaces:
        lines.extend(f"- `{surface}`" for surface in result.durable_surfaces)
    else:
        lines.append("- No durable surfaces identified.")
    return "\n".join(lines).rstrip() + "\n"


def promotion_blocking_details(result: KnowledgePromotionResult) -> list[str]:
    details: list[str] = []
    for finding in result.findings:
        if finding.status not in {"blocked", "waiting"}:
            continue
        if finding.evidence:
            details.extend(f"{finding.area}: {value}" for value in finding.evidence)
        else:
            details.append(f"{finding.area}: {finding.summary}")
    return dedupe_strings(details)


def knowledge_promotion_result_to_dict(result: KnowledgePromotionResult) -> dict[str, Any]:
    return asdict(result)


def strip_suffix(value: str, suffix: str) -> str:
    return value[: -len(suffix)] if value.endswith(suffix) else value


def is_likely_ticker(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", value))


def clean_cell(value: str) -> str:
    return " ".join(str(value).replace("|", "/").split())


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result
