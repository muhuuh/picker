from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from .artifact_hygiene import write_archive_proposals_for_run
from .memory import relative_to_root
from .memory_reflection import (
    build_recurring_failure_report,
    build_run_reflection,
    write_recurring_failure_report,
    write_run_reflection,
)
from .memory_updates import build_memory_update_draft, write_memory_update_draft
from .repo import find_repo_root


@dataclass(frozen=True)
class RunFinalization:
    run_id: str
    run_dir: str
    generated_at: str
    status: str
    metrics: dict[str, Any]
    artifacts: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)


def finalize_run(
    root: Path | None,
    run_id: str,
    current_date: date | None = None,
    recurring_threshold: int = 2,
    archive_after_days: int = 30,
) -> tuple[RunFinalization, tuple[Path, Path]]:
    repo_root = find_repo_root(root)
    today = current_date or date.today()

    reflection = build_run_reflection(repo_root, run_id, today)
    reflection_paths = write_run_reflection(repo_root, reflection)

    recurring_report = build_recurring_failure_report(repo_root, recurring_threshold, today)
    recurring_paths = write_recurring_failure_report(repo_root, recurring_report)
    memory_update_draft = build_memory_update_draft(repo_root, run_id, today)
    memory_update_draft_paths = write_memory_update_draft(repo_root, memory_update_draft)
    archive_proposals_path, archive_candidate_count = write_archive_proposals_for_run(
        repo_root=repo_root,
        run_id=run_id,
        current_date=today,
        archive_after_days=archive_after_days,
    )

    artifacts = [
        relative_to_root(repo_root, path).as_posix()
        for path in (*reflection_paths, *recurring_paths, *memory_update_draft_paths)
    ]
    artifacts.append(archive_proposals_path)
    metrics = {
        "reflection_issues": len(reflection.issues),
        "reflection_memory_update_proposals": len(reflection.memory_update_proposals),
        "recurring_failure_patterns": len(recurring_report.patterns),
        "recurring_memory_update_proposals": len(recurring_report.memory_update_proposals),
        "memory_update_drafts": len(memory_update_draft.items),
        "ready_memory_update_drafts": len([item for item in memory_update_draft.items if item.status == "ready"]),
        "recurring_runs_scanned": recurring_report.runs_scanned,
        "recurring_threshold": recurring_report.threshold,
        "evidence_packets": reflection.metrics.get("evidence_packets", 0),
        "valid_evidence_packets": reflection.metrics.get("valid_evidence_packets", 0),
        "invalid_evidence_packets": reflection.metrics.get("invalid_evidence_packets", 0),
        "archive_candidates": archive_candidate_count,
        "archive_after_days": archive_after_days,
    }
    status = "needs_review" if reflection.issues or recurring_report.patterns else "complete"
    finalization = RunFinalization(
        run_id=run_id,
        run_dir=reflection.run_dir,
        generated_at=today.isoformat(),
        status=status,
        metrics=metrics,
        artifacts=artifacts,
        next_actions=build_next_actions(reflection, recurring_report, archive_candidate_count),
    )
    finalization_paths = write_run_finalization(repo_root, finalization)
    return finalization, finalization_paths


def write_run_finalization(root: Path | None, finalization: RunFinalization) -> tuple[Path, Path]:
    repo_root = find_repo_root(root)
    run_dir = repo_root / finalization.run_dir
    json_path = run_dir / "finalization.json"
    md_path = run_dir / "finalization.md"
    json_path.write_text(json.dumps(finalization_to_dict(finalization), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_finalization_markdown(finalization), encoding="utf-8")
    return json_path, md_path


def finalization_to_dict(finalization: RunFinalization) -> dict[str, Any]:
    return asdict(finalization)


def format_finalization_markdown(finalization: RunFinalization) -> str:
    lines = [
        f"# Run Finalization: {finalization.run_id}",
        "",
        f"Generated: {finalization.generated_at}",
        f"Status: {finalization.status}",
        "",
        "## Metrics",
        "",
    ]
    for key, value in finalization.metrics.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Artifacts", ""])
    for artifact in finalization.artifacts:
        lines.append(f"- `{artifact}`")
    lines.extend(["", "## Next Actions", ""])
    for action in finalization.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def build_next_actions(reflection, recurring_report, archive_candidate_count: int = 0) -> list[str]:
    actions: list[str] = []
    if reflection.issues:
        actions.append("Review `memory_reflection.md` before treating the run as complete.")
    if reflection.memory_update_proposals:
        actions.append("Apply or reject proposed memory updates from `memory_reflection.md`.")
    if recurring_report.patterns:
        actions.append("Review `agents/memory/recurring_failures.md` for repeated workflow issues.")
    if recurring_report.memory_update_proposals:
        actions.append("Apply or reject recurring-failure memory proposals.")
    if getattr(reflection, "memory_update_proposals", None) or getattr(recurring_report, "memory_update_proposals", None):
        actions.append("Review `memory_update_drafts.md` and apply approved ready drafts with `memory apply-updates`.")
    if archive_candidate_count:
        actions.append("Review `archive_proposals.md`; move eligible stale artifacts with `artifact-hygiene archive --write`.")
    if not actions:
        actions.append("No deterministic learning-loop issues found.")
    return actions
