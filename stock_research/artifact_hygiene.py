from __future__ import annotations

import json
import shutil
import subprocess
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


@dataclass(frozen=True)
class RuntimeCleanupRun:
    run_id: str
    status: str
    reason: str
    age_days: int | None
    json_file_count: int
    json_total_bytes: int
    deleted_file_count: int = 0
    deleted_total_bytes: int = 0
    blocked_paths: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RuntimeCleanupResult:
    generated_at: str
    status: str
    mode: str
    retention_days: int
    runs: list[RuntimeCleanupRun]
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


def cleanup_runtime_json(
    *,
    root: Path | None = None,
    current_date: date | None = None,
    write: bool = False,
    retention_days: int = 30,
    run_ids: list[str] | None = None,
) -> RuntimeCleanupResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    selected_run_ids = set(run_ids or [])
    runs_root = repo_root / "agents" / "runs"
    open_refs = load_open_review_references(repo_root)
    tracked_json_paths = git_tracked_paths(repo_root, "agents/runs")
    ignored_json_paths = git_ignored_paths(repo_root, "agents/runs")
    runs: list[RuntimeCleanupRun] = []
    findings: list[str] = []

    if retention_days < 0:
        raise ValueError("retention_days must be >= 0")

    if not runs_root.exists():
        return RuntimeCleanupResult(
            generated_at=today.isoformat(),
            status="no_runtime_json",
            mode="write" if write else "dry_run",
            retention_days=retention_days,
            runs=[],
        )

    for run_dir in sorted(path for path in runs_root.iterdir() if path.is_dir()):
        if selected_run_ids and run_dir.name not in selected_run_ids:
            continue
        json_files = sorted(path for path in run_dir.rglob("*.json") if path.is_file())
        if not json_files:
            continue
        rel_json = [relative_path(repo_root, path) for path in json_files]
        total_bytes = sum(path.stat().st_size for path in json_files)
        status, reason, blocked_paths = classify_runtime_cleanup_run(
            repo_root=repo_root,
            run_dir=run_dir,
            json_paths=rel_json,
            open_refs=open_refs,
            tracked_paths=tracked_json_paths,
            ignored_paths=ignored_json_paths,
            current_date=today,
            retention_days=retention_days,
        )
        deleted_count = 0
        deleted_bytes = 0
        if status == "cleanup_candidate" and write:
            for path in json_files:
                deleted_bytes += path.stat().st_size
                path.unlink()
                deleted_count += 1
                prune_empty_parents(path.parent, stop_at=run_dir)
            status = "deleted"
            reason = "Deleted ignored runtime JSON after knowledge promotion and cleanup guardrails passed."
        elif status == "cleanup_candidate":
            status = "planned"

        runs.append(
            RuntimeCleanupRun(
                run_id=run_dir.name,
                status=status,
                reason=reason,
                age_days=artifact_age_days(run_dir.name, today),
                json_file_count=len(json_files),
                json_total_bytes=total_bytes,
                deleted_file_count=deleted_count,
                deleted_total_bytes=deleted_bytes,
                blocked_paths=blocked_paths,
            )
        )

    if selected_run_ids:
        found = {run.run_id for run in runs}
        missing = sorted(selected_run_ids - found)
        findings.extend(f"No runtime JSON files found for requested run id: {run_id}" for run_id in missing)

    written_paths: list[str] = []
    if write:
        written_paths.append(write_runtime_cleanup_report(repo_root, today, retention_days, runs, findings))

    statuses = {run.status for run in runs}
    if not runs:
        status = "no_runtime_json"
    elif statuses <= {"planned"}:
        status = "ready_to_clean"
    elif statuses <= {"deleted"}:
        status = "complete"
    elif "planned" in statuses or "deleted" in statuses:
        status = "partial"
    elif statuses <= {"recent_keep", "blocked"}:
        status = "no_cleanup_candidates"
    else:
        status = "partial"

    return RuntimeCleanupResult(
        generated_at=today.isoformat(),
        status=status,
        mode="write" if write else "dry_run",
        retention_days=retention_days,
        runs=runs,
        written_paths=written_paths,
        findings=dedupe_strings(findings),
    )


def classify_runtime_cleanup_run(
    *,
    repo_root: Path,
    run_dir: Path,
    json_paths: list[str],
    open_refs: set[str],
    tracked_paths: set[str],
    ignored_paths: set[str] | None,
    current_date: date,
    retention_days: int,
) -> tuple[str, str, list[str]]:
    rel_run = relative_path(repo_root, run_dir)
    age_days = artifact_age_days(run_dir.name, current_date)
    if age_days is not None and age_days < retention_days:
        return "recent_keep", f"Run is {age_days} day(s) old; retention is {retention_days}.", []

    open_ref_matches = sorted(ref for ref in open_refs if ref.startswith(rel_run) or rel_run.startswith(ref))
    if open_ref_matches:
        return "blocked", "Run is referenced by open human-review context.", open_ref_matches

    tracked_matches = sorted(path for path in json_paths if path in tracked_paths)
    if tracked_matches:
        return "blocked", "One or more JSON files are tracked by Git; remove from Git tracking before runtime cleanup.", tracked_matches

    if ignored_paths is not None:
        non_ignored_matches = sorted(path for path in json_paths if path not in ignored_paths)
        if non_ignored_matches:
            return "blocked", "One or more JSON files are not ignored by Git; cleanup only handles ignored runtime JSON.", non_ignored_matches

    required_missing = [
        relative_path(repo_root, run_dir / name)
        for name in ("run_summary.md", "quality_report.md", "memory_reflection.md", "finalization.md")
        if not run_or_archived_artifact(repo_root, run_dir.name, name).exists()
    ]
    if required_missing:
        return "blocked", "Run is missing required markdown/finalization artifacts.", required_missing

    pending_memory_drafts = pending_ready_memory_drafts(run_dir)
    if pending_memory_drafts:
        return "blocked", "Run has ready memory-update drafts that should be applied or rejected first.", pending_memory_drafts

    missing_final_reports = missing_human_final_reports(repo_root, run_dir)
    if missing_final_reports:
        return "blocked", "Run has human synthesis packs without canonical final human reports.", missing_final_reports

    from .knowledge_promotion import assess_knowledge_promotion, promotion_blocking_details

    promotion = assess_knowledge_promotion(
        root=repo_root,
        run_id=run_dir.name,
        current_date=current_date,
        write=False,
    )
    if not promotion.cleanup_ready:
        return (
            "blocked",
            f"Run knowledge promotion is not complete ({promotion.status}).",
            promotion_blocking_details(promotion),
        )

    return "cleanup_candidate", "Runtime JSON is eligible for cleanup; markdown/final artifacts preserve the review trail.", []


def pending_ready_memory_drafts(run_dir: Path) -> list[str]:
    path = run_dir / "memory_update_drafts.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [path.name]
    result: list[str] = []
    for item in data.get("items", []):
        if str(item.get("status", "")).lower() == "ready":
            result.append(str(item.get("proposal_id", "ready_memory_update")))
    return result


def missing_human_final_reports(repo_root: Path, run_dir: Path) -> list[str]:
    synthesis_dir = run_dir / "reports" / "human_synthesis"
    if not synthesis_dir.exists():
        return []
    missing: list[str] = []
    for pack in sorted(synthesis_dir.glob("*_synthesis_pack.md")):
        ticker = pack.name.replace("_synthesis_pack.md", "")
        final_report = pack.with_name(f"{ticker}_final_human_report.md")
        final_rel = final_report.relative_to(run_dir).as_posix()
        if not run_or_archived_artifact(repo_root, run_dir.name, final_rel).exists():
            missing.append(relative_path(repo_root, final_report))
    return missing


def run_or_archived_artifact(repo_root: Path, run_id: str, rel_inside_run: str) -> Path:
    active = repo_root / "agents" / "runs" / run_id / rel_inside_run
    if active.exists():
        return active
    year = run_id[:4] if run_id[:4].isdigit() else "unknown"
    archived = repo_root / "archive" / "runs" / year / run_id / rel_inside_run
    return archived if archived.exists() else active


def git_tracked_paths(repo_root: Path, pathspec: str) -> set[str]:
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return set()
    try:
        result = subprocess.run(
            ["git", "ls-files", pathspec],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return set()
    if result.returncode != 0:
        return set()
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip().endswith(".json")}


def git_ignored_paths(repo_root: Path, pathspec: str) -> set[str] | None:
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return None
    try:
        result = subprocess.run(
            ["git", "ls-files", "-o", "-i", "--exclude-standard", pathspec],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip().endswith(".json")}


def write_runtime_cleanup_report(
    repo_root: Path,
    current_date: date,
    retention_days: int,
    runs: list[RuntimeCleanupRun],
    findings: list[str],
) -> str:
    path = repo_root / "archive" / "runtime_cleanup_report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Runtime JSON Cleanup Report",
        "",
        f"Generated: {current_date.isoformat()}",
        f"Retention days: {retention_days}",
        "",
        "This report records cleanup of ignored generated JSON under `agents/runs/`. It does not archive or delete markdown review artifacts.",
        "",
        "| Status | Run ID | Age Days | JSON Files | JSON KB | Deleted Files | Deleted KB | Reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for run in runs:
        lines.append(
            "| "
            + " | ".join(
                clean_cell(value)
                for value in [
                    run.status,
                    run.run_id,
                    "" if run.age_days is None else str(run.age_days),
                    str(run.json_file_count),
                    f"{run.json_total_bytes / 1024:.1f}",
                    str(run.deleted_file_count),
                    f"{run.deleted_total_bytes / 1024:.1f}",
                    run.reason,
                ]
            )
            + " |"
        )
    if not runs:
        lines.append("| no_runtime_json |  |  |  |  |  |  | No ignored runtime JSON files matched the request. |")
    blocked = [run for run in runs if run.blocked_paths]
    if blocked:
        lines.extend(["", "## Blocked Details", ""])
        for run in blocked:
            lines.append(f"### {run.run_id}")
            lines.extend(f"- `{path}`" for path in run.blocked_paths)
            lines.append("")
    if findings:
        lines.extend(["", "## Findings", ""])
        lines.extend(f"- {finding}" for finding in findings)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return relative_path(repo_root, path)


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


def runtime_cleanup_result_to_dict(result: RuntimeCleanupResult) -> dict:
    return asdict(result)


def dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result
