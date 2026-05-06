from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from .analysis_runner import AnalysisExecutor, run_analysis_tasks
from .manifest import build_weekly_manifest, write_manifest
from .memory import relative_to_root
from .memory_llm_writer import (
    DEFAULT_MEMORY_WRITER_MODEL,
    MemoryWriterReview,
    build_memory_writer_review,
    memory_writer_review_to_dict,
)
from .provider_runner import ProviderExecutor, run_provider_tasks
from .quality_report import build_quality_report, quality_report_to_dict, write_quality_report
from .repo import find_repo_root, load_repo_state
from .run_finalization import RunFinalization, finalize_run, finalization_to_dict
from .run_summary import RunSummary, build_run_summary, run_summary_to_dict, write_run_summary


@dataclass(frozen=True)
class ScheduledRunResult:
    run_id: str
    generated_at: str
    status: str
    mode: str
    steps: dict[str, Any]
    artifacts: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)


def run_weekly_research_workflow(
    root: Path | None = None,
    current_date: date | None = None,
    write: bool = False,
    execute_providers: bool = False,
    execute_analysis: bool = False,
    execute_memory_writer: bool = False,
    update_memory_drafts: bool = True,
    recurring_threshold: int = 2,
    memory_writer_model: str = DEFAULT_MEMORY_WRITER_MODEL,
    provider_executor: ProviderExecutor | None = None,
    analysis_executor: AnalysisExecutor | None = None,
    memory_writer_responder=None,
) -> tuple[ScheduledRunResult, list[Path]]:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    state = load_repo_state(repo_root)
    manifest = build_weekly_manifest(state, today)
    run_id = f"{manifest['run_date']}_weekly"
    artifacts: list[Path] = []

    manifest_path: Path | None = None
    if write:
        manifest_path = write_manifest(state, manifest)
        artifacts.append(manifest_path)

    provider_result = run_provider_tasks(
        root=repo_root,
        manifest=manifest,
        execute=execute_providers,
        current_date=today,
        executor=provider_executor,
    )
    analysis_result = run_analysis_tasks(
        root=repo_root,
        manifest=manifest,
        execute=execute_analysis,
        current_date=today,
        executor=analysis_executor,
    )

    run_summary: RunSummary | None = None
    quality_report = None
    finalization: RunFinalization | None = None
    memory_writer_review: MemoryWriterReview | None = None

    if write:
        run_summary = build_run_summary(repo_root, run_id, today)
        artifacts.extend(write_run_summary(repo_root, run_summary))

        quality_report = build_quality_report(repo_root, run_id, today)
        artifacts.extend(write_quality_report(repo_root, quality_report))

        finalization, finalization_paths = finalize_run(
            root=repo_root,
            run_id=run_id,
            current_date=today,
            recurring_threshold=recurring_threshold,
        )
        artifacts.extend(finalization_paths)

        memory_writer_review, memory_writer_paths = build_memory_writer_review(
            root=repo_root,
            run_id=run_id,
            current_date=today,
            execute=execute_memory_writer,
            model=memory_writer_model,
            update_drafts=update_memory_drafts,
            responder=memory_writer_responder,
            write_artifacts=True,
        )
        artifacts.extend(memory_writer_paths)

    result = ScheduledRunResult(
        run_id=run_id,
        generated_at=today.isoformat(),
        status=determine_status(write, provider_result, analysis_result, quality_report, finalization),
        mode=run_mode(write, execute_providers, execute_analysis, execute_memory_writer),
        steps=build_steps(
            manifest=manifest,
            manifest_path=manifest_path,
            provider_result=provider_result,
            analysis_result=analysis_result,
            run_summary=run_summary,
            quality_report=quality_report,
            finalization=finalization,
            memory_writer_review=memory_writer_review,
        ),
        artifacts=[relative_to_root(repo_root, path).as_posix() for path in artifacts],
        next_actions=next_actions(write, provider_result, analysis_result, quality_report, finalization),
    )

    if write:
        artifacts.extend(write_scheduled_run_report(repo_root, result))

    return result, artifacts


def determine_status(
    write: bool,
    provider_result: dict[str, Any],
    analysis_result: dict[str, Any],
    quality_report,
    finalization: RunFinalization | None,
) -> str:
    if not write:
        return "dry_run"
    if provider_result.get("errors") or analysis_result.get("errors") or analysis_result.get("skipped"):
        return "needs_review"
    if quality_report and quality_report.findings:
        return "needs_review"
    if finalization and finalization.status != "complete":
        return finalization.status
    return "complete"


def run_mode(write: bool, execute_providers: bool, execute_analysis: bool, execute_memory_writer: bool) -> str:
    if not write:
        return "dry_run"
    flags = [
        "providers_execute" if execute_providers else "providers_dry_run",
        "analysis_execute" if execute_analysis else "analysis_dry_run",
        "memory_writer_execute" if execute_memory_writer else "memory_writer_deterministic",
    ]
    return ", ".join(flags)


def build_steps(
    manifest: dict[str, Any],
    manifest_path: Path | None,
    provider_result: dict[str, Any],
    analysis_result: dict[str, Any],
    run_summary: RunSummary | None,
    quality_report,
    finalization: RunFinalization | None,
    memory_writer_review: MemoryWriterReview | None,
) -> dict[str, Any]:
    return {
        "manifest": {
            "status": "written" if manifest_path else "built",
            "path": str(manifest_path) if manifest_path else "",
            "provider_tasks": len(manifest.get("provider_tasks", [])),
            "analysis_tasks": len(manifest.get("analysis_tasks", [])),
        },
        "provider_tasks": provider_result,
        "analysis_tasks": analysis_result,
        "run_summary": run_summary_to_dict(run_summary) if run_summary else {"status": "not_written"},
        "quality_report": quality_report_to_dict(quality_report) if quality_report else {"status": "not_written"},
        "memory_finalization": finalization_to_dict(finalization) if finalization else {"status": "not_written"},
        "memory_writer_review": memory_writer_review_to_dict(memory_writer_review) if memory_writer_review else {"status": "not_written"},
        "framework_boundary": {
            "status": "pending_decision",
            "next_decision": "Choose the agent orchestration framework before adding LLM orchestrator/runtime specialists.",
        },
    }


def next_actions(
    write: bool,
    provider_result: dict[str, Any],
    analysis_result: dict[str, Any],
    quality_report,
    finalization: RunFinalization | None,
) -> list[str]:
    actions: list[str] = []
    if not write:
        actions.append("Re-run with `--write` to persist manifest, reports, finalization, and memory-writer artifacts.")
    if provider_result.get("mode") == "dry_run" and provider_result.get("planned_count", 0):
        actions.append("Use `--execute-providers` when API-backed provider evidence should be gathered.")
    if analysis_result.get("mode") == "dry_run" and analysis_result.get("planned_count", 0):
        actions.append("Use `--execute-analysis` after provider evidence exists.")
    if provider_result.get("errors"):
        actions.append("Review provider task errors before treating the run as complete.")
    if analysis_result.get("errors") or analysis_result.get("skipped"):
        actions.append("Review analysis task errors/skips before synthesis.")
    if quality_report and quality_report.findings:
        actions.append("Review `quality_report.md`; deterministic quality findings remain.")
    if finalization and finalization.next_actions:
        actions.extend(finalization.next_actions)
    actions.append("Next architecture step: choose OpenAI Agents SDK, Pydantic AI, LangGraph, or a hybrid for the LLM orchestrator layer.")
    return unique(actions)


def unique(values: list[str]) -> list[str]:
    seen = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def write_scheduled_run_report(root: Path | None, result: ScheduledRunResult) -> tuple[Path, Path]:
    repo_root = find_repo_root(root)
    run_dir = repo_root / "agents" / "runs" / result.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "orchestration_report.json"
    md_path = run_dir / "orchestration_report.md"
    json_path.write_text(json.dumps(scheduled_run_result_to_dict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_scheduled_run_report_markdown(result), encoding="utf-8")
    return json_path, md_path


def scheduled_run_result_to_dict(result: ScheduledRunResult) -> dict[str, Any]:
    return asdict(result)


def format_scheduled_run_report_markdown(result: ScheduledRunResult) -> str:
    lines = [
        f"# Orchestration Report: {result.run_id}",
        "",
        f"Generated: {result.generated_at}",
        f"Status: {result.status}",
        f"Mode: {result.mode}",
        "",
        "## Step Summary",
        "",
        f"- manifest: {result.steps['manifest']['status']} ({result.steps['manifest']['provider_tasks']} provider task(s), {result.steps['manifest']['analysis_tasks']} analysis task(s))",
        f"- provider_tasks: {result.steps['provider_tasks']['mode']} ({len(result.steps['provider_tasks'].get('executed', []))} executed, {len(result.steps['provider_tasks'].get('errors', []))} error(s))",
        f"- analysis_tasks: {result.steps['analysis_tasks']['mode']} ({len(result.steps['analysis_tasks'].get('executed', []))} executed, {len(result.steps['analysis_tasks'].get('errors', []))} error(s), {len(result.steps['analysis_tasks'].get('skipped', []))} skipped)",
        f"- quality_report: {result.steps['quality_report'].get('metrics', {}).get('findings', 'not_written')} finding(s)",
        f"- memory_finalization: {result.steps['memory_finalization'].get('status', 'not_written')}",
        f"- memory_writer_review: {result.steps['memory_writer_review'].get('mode', 'not_written')}",
        "",
        "## Artifacts",
        "",
    ]
    if result.artifacts:
        for artifact in result.artifacts:
            lines.append(f"- `{artifact}`")
    else:
        lines.append("- No artifacts written.")
    lines.extend(["", "## Next Actions", ""])
    for action in result.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"
