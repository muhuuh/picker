from __future__ import annotations

import shutil
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from .repo import find_repo_root, load_repo_state


REPORT_PATTERNS = (
    "final_digest.md",
    "run_summary.md",
    "quality_report.md",
    "orchestration_report.md",
    "company_file_factual_updates.md",
    "company_research/*_company_research.md",
    "market_research/*.md",
    "reports/opportunity_assessment/*_opportunity_assessment.md",
    "reports/company_news_specialist/*.md",
    "reports/financial_data_specialist/*.md",
    "portfolio_review/*.md",
    "memory_evaluation/*.md",
)


@dataclass(frozen=True)
class ArtifactInventoryItem:
    path: str
    run_id: str
    artifact_type: str
    ticker_or_topic: str
    status: str
    reason: str
    age_days: int | None = None


@dataclass(frozen=True)
class ArtifactInventoryResult:
    generated_at: str
    status: str
    active_tickers: list[str]
    open_review_reference_count: int
    items: list[ArtifactInventoryItem]
    written_paths: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ArchiveMoveItem:
    source_path: str
    archive_path: str
    status: str
    reason: str


@dataclass(frozen=True)
class ArchiveMoveResult:
    generated_at: str
    status: str
    mode: str
    archive_after_days: int
    items: list[ArchiveMoveItem]
    written_paths: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)


def build_artifact_inventory(
    *,
    root: Path | None = None,
    current_date: date | None = None,
    write: bool = False,
    archive_after_days: int = 30,
) -> ArtifactInventoryResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    active_tickers = load_active_tickers(repo_root)
    open_refs = load_open_review_references(repo_root)
    items: list[ArtifactInventoryItem] = []

    runs_root = repo_root / "agents" / "runs"
    if runs_root.exists():
        for run_dir in sorted(path for path in runs_root.iterdir() if path.is_dir()):
            for artifact in iter_report_artifacts(run_dir):
                rel = relative_path(repo_root, artifact)
                artifact_type, ticker_or_topic = classify_artifact(artifact, run_dir)
                age_days = artifact_age_days(run_dir.name, today)
                status, reason = classify_status(
                    rel,
                    artifact_type,
                    ticker_or_topic,
                    active_tickers,
                    open_refs,
                    age_days,
                    archive_after_days,
                )
                items.append(
                    ArtifactInventoryItem(
                        path=rel,
                        run_id=run_dir.name,
                        artifact_type=artifact_type,
                        ticker_or_topic=ticker_or_topic,
                        status=status,
                        reason=reason,
                        age_days=age_days,
                    )
                )
    archived_root = repo_root / "archive" / "runs"
    if archived_root.exists():
        for artifact in sorted(archived_root.glob("*/*/**/*.md")):
            parsed = parse_archived_artifact(repo_root, artifact)
            if parsed is None:
                continue
            run_id, rel_inside_run = parsed
            artifact_type, ticker_or_topic = classify_artifact_rel(rel_inside_run)
            items.append(
                ArtifactInventoryItem(
                    path=relative_path(repo_root, artifact),
                    run_id=run_id,
                    artifact_type=artifact_type,
                    ticker_or_topic=ticker_or_topic,
                    status="archived",
                    reason="Artifact has already been moved into archive/runs.",
                    age_days=artifact_age_days(run_id, today),
                )
            )

    written_paths: list[str] = []
    if write:
        written_paths.append(write_research_index(repo_root, today, items, active_tickers, open_refs))

    if not items:
        status = "empty"
    elif any(item.status == "review_blocked" for item in items):
        status = "needs_review"
    else:
        status = "complete"
    return ArtifactInventoryResult(
        generated_at=today.isoformat(),
        status=status,
        active_tickers=active_tickers,
        open_review_reference_count=len(open_refs),
        items=items,
        written_paths=written_paths,
    )


def iter_report_artifacts(run_dir: Path) -> Iterable[Path]:
    seen: set[Path] = set()
    for pattern in REPORT_PATTERNS:
        for path in run_dir.glob(pattern):
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            yield path


def load_active_tickers(repo_root: Path) -> list[str]:
    state = load_repo_state(repo_root)
    tickers: list[str] = []
    for table_name in ("current_holdings", "monitoring"):
        table = state.stock_tables.get(table_name)
        if not table:
            continue
        for row in table.rows:
            ticker = str(row.get("ticker", "")).strip().upper()
            if ticker and ticker not in tickers:
                tickers.append(ticker)
    return tickers


def load_open_review_references(repo_root: Path) -> set[str]:
    state = load_repo_state(repo_root)
    refs: set[str] = set()
    for item in state.human_review_items:
        status = str(item.get("Status", "") or item.get("status", "")).strip().lower()
        if status in {"approved", "rejected", "done", "closed"}:
            continue
        for value in item.values():
            text = str(value)
            for token in text.replace(")", " ").replace("(", " ").replace(",", " ").split():
                if token.startswith("agents/runs/") or token.startswith("market_research/"):
                    refs.add(token.strip("`[]"))
    return refs


def classify_artifact(path: Path, run_dir: Path) -> tuple[str, str]:
    return classify_artifact_rel(path.relative_to(run_dir).as_posix())


def classify_artifact_rel(rel: str) -> tuple[str, str]:
    path = Path(rel)
    stem = path.stem
    if rel.startswith("reports/opportunity_assessment/"):
        return "opportunity_assessment", stem.replace("_opportunity_assessment", "").upper()
    if rel.startswith("company_research/"):
        return "company_research", stem.replace("_company_research", "").upper()
    if rel.startswith("market_research/"):
        return "market_research", stem
    if rel == "final_digest.md":
        return "final_digest", "weekly"
    if rel == "company_file_factual_updates.md":
        return "company_file_fyi", "weekly"
    if rel.startswith("reports/company_news_specialist/"):
        return "company_news_review", stem.replace("_company_news_review", "").upper()
    if rel.startswith("reports/financial_data_specialist/"):
        return "financial_review", stem.replace("_financial_review", "").upper()
    if rel.startswith("portfolio_review/"):
        return "portfolio_review", "portfolio"
    if rel.startswith("memory_evaluation/"):
        return "memory_evaluation", "memory"
    return stem, "run"


def parse_archived_artifact(repo_root: Path, path: Path) -> tuple[str, str] | None:
    try:
        rel_parts = path.resolve().relative_to((repo_root / "archive" / "runs").resolve()).parts
    except ValueError:
        return None
    if len(rel_parts) < 3:
        return None
    run_id = rel_parts[1]
    rel_inside_run = Path(*rel_parts[2:]).as_posix()
    return run_id, rel_inside_run


def archive_artifacts(
    *,
    root: Path | None = None,
    current_date: date | None = None,
    write: bool = False,
    archive_after_days: int = 30,
    limit: int | None = None,
) -> ArchiveMoveResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    inventory = build_artifact_inventory(
        root=repo_root,
        current_date=today,
        write=False,
        archive_after_days=archive_after_days,
    )
    candidates = [item for item in inventory.items if item.status == "archive_candidate"]
    if limit is not None:
        candidates = candidates[:limit]
    items: list[ArchiveMoveItem] = []
    findings: list[str] = []

    for candidate in candidates:
        source = repo_root / candidate.path
        archive_path, reason = archive_destination_for(repo_root, candidate)
        if not source.exists():
            if archive_path.exists():
                items.append(
                    ArchiveMoveItem(
                        source_path=candidate.path,
                        archive_path=relative_path(repo_root, archive_path),
                        status="already_archived",
                        reason="Source is missing and archive destination exists.",
                    )
                )
                continue
            items.append(
                ArchiveMoveItem(
                    source_path=candidate.path,
                    archive_path=relative_path(repo_root, archive_path),
                    status="blocked",
                    reason="Source artifact is missing.",
                )
            )
            continue
        safety_findings = archive_safety_findings(repo_root, source, archive_path)
        if safety_findings:
            findings.extend(safety_findings)
            items.append(
                ArchiveMoveItem(
                    source_path=candidate.path,
                    archive_path=relative_path(repo_root, archive_path),
                    status="blocked",
                    reason="; ".join(safety_findings),
                )
            )
            continue
        if archive_path.exists():
            items.append(
                ArchiveMoveItem(
                    source_path=candidate.path,
                    archive_path=relative_path(repo_root, archive_path),
                    status="blocked",
                    reason="Archive destination already exists.",
                )
            )
            continue
        if write:
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(archive_path))
            prune_empty_parents(source.parent, stop_at=(repo_root / "agents" / "runs" / candidate.run_id))
        items.append(
            ArchiveMoveItem(
                source_path=candidate.path,
                archive_path=relative_path(repo_root, archive_path),
                status="moved" if write else "planned",
                reason=reason,
            )
        )

    written_paths: list[str] = []
    if write:
        written_paths.append(write_archive_move_report(repo_root, today, archive_after_days, items, findings))
        refreshed = build_artifact_inventory(
            root=repo_root,
            current_date=today,
            write=True,
            archive_after_days=archive_after_days,
        )
        written_paths.extend(refreshed.written_paths)

    statuses = {item.status for item in items}
    if not items:
        status = "no_archive_candidates"
    elif statuses <= {"planned"}:
        status = "ready_to_archive"
    elif statuses <= {"moved", "already_archived"}:
        status = "complete"
    elif "blocked" in statuses:
        status = "blocked"
    else:
        status = "partial"
    return ArchiveMoveResult(
        generated_at=today.isoformat(),
        status=status,
        mode="write" if write else "dry_run",
        archive_after_days=archive_after_days,
        items=items,
        written_paths=dedupe_strings(written_paths),
        findings=dedupe_strings(findings),
    )


def write_archive_proposals_for_run(
    *,
    repo_root: Path,
    run_id: str,
    current_date: date,
    archive_after_days: int = 30,
) -> tuple[str, int]:
    inventory = build_artifact_inventory(
        root=repo_root,
        current_date=current_date,
        write=False,
        archive_after_days=archive_after_days,
    )
    candidates = [item for item in inventory.items if item.status == "archive_candidate"]
    run_dir = repo_root / "agents" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "archive_proposals.md"
    lines = [
        f"# Archive Proposals: {run_id}",
        "",
        f"Generated: {current_date.isoformat()}",
        f"Archive threshold: {archive_after_days} day(s)",
        "",
        "These are stale or inactive markdown run artifacts that can be moved to `archive/runs/` after review. Active tickers and open human-review context are excluded.",
        "",
        "| Run ID | Type | Ticker / Topic | Age Days | Artifact | Reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in candidates:
        lines.append(
            "| "
            + " | ".join(
                clean_cell(value)
                for value in [
                    item.run_id,
                    item.artifact_type,
                    item.ticker_or_topic,
                    "" if item.age_days is None else str(item.age_days),
                    f"[{item.path}]({item.path})",
                    item.reason,
                ]
            )
            + " |"
        )
    if not candidates:
        lines.append("|  |  |  |  |  | No archive candidates matched the current guardrails. |")
    lines.extend(
        [
            "",
            "## Follow-Up",
            "",
            "- Dry-run archive moves with `python -m stock_research artifact-hygiene archive`.",
            "- Move only eligible candidates with `python -m stock_research artifact-hygiene archive --write`.",
            "- The archive command refreshes `archive/research_index.md` after moving files.",
        ]
    )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return relative_path(repo_root, path), len(candidates)


def archive_destination_for(repo_root: Path, item: ArtifactInventoryItem) -> tuple[Path, str]:
    source = repo_root / item.path
    run_dir = repo_root / "agents" / "runs" / item.run_id
    try:
        rel_inside_run = source.resolve().relative_to(run_dir.resolve())
    except ValueError:
        rel_inside_run = Path(source.name)
    year = item.run_id[:4] if item.run_id[:4].isdigit() else "unknown"
    destination = repo_root / "archive" / "runs" / year / item.run_id / rel_inside_run
    return destination, item.reason


def archive_safety_findings(repo_root: Path, source: Path, archive_path: Path) -> list[str]:
    findings: list[str] = []
    try:
        source.resolve().relative_to((repo_root / "agents" / "runs").resolve())
    except ValueError:
        findings.append(f"Refusing to archive source outside agents/runs: {relative_path(repo_root, source)}")
    try:
        archive_path.resolve().relative_to((repo_root / "archive" / "runs").resolve())
    except ValueError:
        findings.append(f"Refusing archive destination outside archive/runs: {relative_path(repo_root, archive_path)}")
    if source.suffix.lower() != ".md":
        findings.append("Only markdown report artifacts are archive-move candidates.")
    if "stock_tracking/stock_info_files" in source.as_posix():
        findings.append("Refusing to archive stock_info_files.")
    return findings


def prune_empty_parents(path: Path, *, stop_at: Path) -> None:
    current = path
    stop = stop_at.resolve()
    while current.exists() and current.resolve() != stop:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def write_archive_move_report(
    repo_root: Path,
    current_date: date,
    archive_after_days: int,
    items: list[ArchiveMoveItem],
    findings: list[str],
) -> str:
    path = repo_root / "archive" / "archive_move_report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Archive Move Report",
        "",
        f"Generated: {current_date.isoformat()}",
        f"Archive threshold: {archive_after_days} day(s)",
        "",
        "| Status | Source | Archive Path | Reason |",
        "| --- | --- | --- | --- |",
    ]
    for item in items:
        lines.append(
            "| "
            + " | ".join(
                clean_cell(value)
                for value in [
                    item.status,
                    f"[{item.source_path}]({item.source_path})",
                    f"[{item.archive_path}]({item.archive_path})",
                    item.reason,
                ]
            )
            + " |"
        )
    if not items:
        lines.append("| no_archive_candidates |  |  | No archive candidates matched the current guardrails. |")
    if findings:
        lines.extend(["", "## Findings", ""])
        lines.extend(f"- {finding}" for finding in findings)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return relative_path(repo_root, path)


def classify_status(
    path: str,
    artifact_type: str,
    ticker_or_topic: str,
    active_tickers: list[str],
    open_refs: set[str],
    age_days: int | None,
    archive_after_days: int,
) -> tuple[str, str]:
    if any(path.startswith(ref) or ref.startswith(path) for ref in open_refs):
        return "review_blocked", "Referenced by an open human-review item."
    if ticker_or_topic.upper() in active_tickers:
        return "active_keep", "Ticker is in current holdings or monitoring."
    if artifact_type in {"final_digest", "portfolio_review", "company_file_fyi"}:
        return "active_keep", "Run-level artifact remains useful for the latest weekly review trail."
    if age_days is not None and age_days < archive_after_days:
        return "recent_keep", f"Artifact is {age_days} day(s) old; archive threshold is {archive_after_days}."
    return "archive_candidate", "No active ticker or open-review reference keeps this artifact in the active set."


def artifact_age_days(run_id: str, current_date: date) -> int | None:
    prefix = run_id[:10]
    try:
        return (current_date - datetime.strptime(prefix, "%Y-%m-%d").date()).days
    except ValueError:
        return None


def write_research_index(
    repo_root: Path,
    current_date: date,
    items: list[ArtifactInventoryItem],
    active_tickers: list[str],
    open_refs: set[str],
) -> str:
    archive_dir = repo_root / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    path = archive_dir / "research_index.md"
    lines = [
        "# Research Artifact Index",
        "",
        f"Generated: {current_date.isoformat()}",
        "",
        "This file indexes research artifacts so active reports remain findable and old or inactive artifacts can be archived later without deletion.",
        "",
        f"Active tickers: {', '.join(active_tickers) if active_tickers else 'none'}",
        f"Open review references tracked: {len(open_refs)}",
        "",
        "| Status | Run ID | Type | Ticker / Topic | Age Days | Artifact | Reason |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in items:
        lines.append(
            "| "
            + " | ".join(
                clean_cell(value)
                for value in [
                    item.status,
                    item.run_id,
                    item.artifact_type,
                    item.ticker_or_topic,
                    "" if item.age_days is None else str(item.age_days),
                    f"[{item.path}]({item.path})",
                    item.reason,
                ]
            )
            + " |"
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return relative_path(repo_root, path)


def clean_cell(value: str) -> str:
    return " ".join(str(value).replace("|", "/").split())


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def artifact_inventory_to_dict(result: ArtifactInventoryResult) -> dict:
    return asdict(result)


def archive_move_result_to_dict(result: ArchiveMoveResult) -> dict:
    return asdict(result)


def dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result
