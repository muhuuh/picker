from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from .agent_runtime.context import build_research_run_context
from .agent_runtime.proposal_review import build_proposal_review, proposal_review_to_dict
from .agent_runtime.reports import build_orchestrator_input, output_status, output_to_dict
from .agent_runtime.runner import AgentRuntimeResult, run_agent_sync
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
    execute_orchestrator: bool = False,
    update_memory_drafts: bool = True,
    recurring_threshold: int = 2,
    memory_writer_model: str = DEFAULT_MEMORY_WRITER_MODEL,
    orchestrator_model: str | None = None,
    provider_executor: ProviderExecutor | None = None,
    analysis_executor: AnalysisExecutor | None = None,
    memory_writer_responder=None,
    orchestrator_executor=None,
) -> tuple[ScheduledRunResult, list[Path]]:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    state = load_repo_state(repo_root)
    manifest = build_weekly_manifest(state, today)
    run_id = f"{manifest['run_date']}_weekly"
    artifacts: list[Path] = []

    if write and (execute_providers or execute_analysis):
        clean_generated_run_artifacts(repo_root, run_id)

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
    orchestrator_result: dict[str, Any] = {"status": "not_run"}
    proposal_review_result: dict[str, Any] = {"status": "not_run"}

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

        if execute_orchestrator:
            context = build_research_run_context(
                root=repo_root,
                run_id=run_id,
                task="main orchestrator",
                manifest_path=manifest_path,
                dry_run=not (execute_providers and execute_analysis),
                execute_providers=execute_providers,
                execute_analysis=execute_analysis,
            )
            prompt = build_orchestrator_input(
                run_id,
                context.memory_item_ids,
                provider_mode=str(provider_result.get("mode", "")),
                analysis_mode=str(analysis_result.get("mode", "")),
            )
            try:
                if orchestrator_executor:
                    sdk_result = orchestrator_executor(context, prompt, orchestrator_model)
                else:
                    sdk_result = run_agent_sync(
                        "main_orchestrator",
                        prompt,
                        context,
                        model=orchestrator_model,
                        write=True,
                    )
                orchestrator_result = agent_runtime_result_to_dict(sdk_result)
                add_scheduled_orchestrator_findings(
                    orchestrator_result,
                    provider_result=provider_result,
                    analysis_result=analysis_result,
                )
                artifacts.extend(Path(path) for path in sdk_result.written_paths)
                if orchestrator_result.get("status") == "complete":
                    proposal_review = build_proposal_review(
                        root=repo_root,
                        run_id=run_id,
                        current_date=today,
                        write=True,
                        queue_review=True,
                    )
                    proposal_review_result = proposal_review_to_dict(proposal_review)
                    artifacts.extend(repo_root / path for path in proposal_review.written_paths)
            except Exception as exc:
                orchestrator_result = {
                    "status": "error",
                    "errors": [str(exc)],
                    "quality_findings": [],
                    "written_paths": [],
                }
                proposal_review_result = {"status": "not_run", "reason": "orchestrator_error"}

    result = ScheduledRunResult(
        run_id=run_id,
        generated_at=today.isoformat(),
        status=determine_status(write, provider_result, analysis_result, quality_report, finalization, orchestrator_result),
        mode=run_mode(write, execute_providers, execute_analysis, execute_memory_writer, execute_orchestrator),
        steps=build_steps(
            manifest=manifest,
            manifest_path=manifest_path,
            provider_result=provider_result,
            analysis_result=analysis_result,
            run_summary=run_summary,
            quality_report=quality_report,
            finalization=finalization,
            memory_writer_review=memory_writer_review,
            orchestrator_result=orchestrator_result,
            proposal_review_result=proposal_review_result,
        ),
        artifacts=[relative_to_root(repo_root, path).as_posix() for path in artifacts],
        next_actions=next_actions(write, provider_result, analysis_result, quality_report, finalization, orchestrator_result),
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
    orchestrator_result: dict[str, Any] | None = None,
) -> str:
    if not write:
        return "dry_run"
    if provider_result.get("errors") or analysis_result.get("errors") or analysis_result.get("skipped"):
        return "needs_review"
    if quality_report and quality_report.findings:
        return "needs_review"
    if finalization and finalization.status != "complete":
        return finalization.status
    if orchestrator_result and orchestrator_result.get("status") in {"error", "needs_review"}:
        return "needs_review"
    return "complete"


def run_mode(
    write: bool,
    execute_providers: bool,
    execute_analysis: bool,
    execute_memory_writer: bool,
    execute_orchestrator: bool,
) -> str:
    if not write:
        return "dry_run"
    flags = [
        "providers_execute" if execute_providers else "providers_dry_run",
        "analysis_execute" if execute_analysis else "analysis_dry_run",
        "memory_writer_execute" if execute_memory_writer else "memory_writer_deterministic",
        "orchestrator_execute" if execute_orchestrator else "orchestrator_not_run",
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
    orchestrator_result: dict[str, Any],
    proposal_review_result: dict[str, Any],
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
        "agent_orchestrator": orchestrator_result,
        "orchestrator_proposal_review": proposal_review_result,
        "framework_boundary": {
            "status": "resolved",
            "framework": "OpenAI Agents SDK",
            "next_step": "Use `--execute-orchestrator` to opt into SDK orchestration after deterministic finalization.",
        },
    }


def next_actions(
    write: bool,
    provider_result: dict[str, Any],
    analysis_result: dict[str, Any],
    quality_report,
    finalization: RunFinalization | None,
    orchestrator_result: dict[str, Any] | None = None,
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
    if not write:
        actions.append("Use `--write --execute-orchestrator` after deterministic artifacts are ready to run SDK synthesis.")
    elif not orchestrator_result or orchestrator_result.get("status") == "not_run":
        actions.append("Use `--execute-orchestrator` to run OpenAI Agents SDK synthesis over the written artifacts.")
    elif orchestrator_result.get("status") == "error":
        actions.append("Review SDK orchestrator errors before treating synthesis as complete.")
    elif orchestrator_result.get("quality_findings"):
        if any("dry-run" in str(finding) for finding in orchestrator_result.get("quality_findings", [])):
            actions.append(
                "Run `--write --execute-providers --execute-analysis --execute-orchestrator` before accepting SDK file updates as fresh research."
            )
        actions.append("Review SDK orchestrator quality findings and tighten prompts/tools before accepting synthesis.")
    return unique(actions)


def agent_runtime_result_to_dict(result: AgentRuntimeResult) -> dict[str, Any]:
    final_status = output_status(result.final_output)
    status = "complete" if not result.quality_findings and final_status == "ready" else "needs_review"
    return {
        "status": status,
        "agent_id": result.agent_id,
        "trace_id": result.trace_id,
        "group_id": result.group_id,
        "quality_findings": result.quality_findings,
        "written_paths": list(result.written_paths),
        "final_output": output_to_dict(result.final_output),
    }


def add_scheduled_orchestrator_findings(
    orchestrator_result: dict[str, Any],
    *,
    provider_result: dict[str, Any],
    analysis_result: dict[str, Any],
) -> None:
    final_output = orchestrator_result.get("final_output") or {}
    if not isinstance(final_output, dict):
        return
    provider_dry_run = provider_result.get("mode") == "dry_run" and provider_result.get("planned_count", 0)
    analysis_dry_run = analysis_result.get("mode") == "dry_run" and analysis_result.get("planned_count", 0)
    if not provider_dry_run and not analysis_dry_run:
        return
    has_actionable_output = bool(final_output.get("file_update_proposals") or final_output.get("alerts"))
    claims_ready = final_output.get("status") == "ready"
    if not has_actionable_output and not claims_ready:
        return
    missing_steps = []
    if provider_dry_run:
        missing_steps.append("provider tasks")
    if analysis_dry_run:
        missing_steps.append("analysis tasks")
    finding = (
        "SDK orchestrator produced ready/actionable synthesis while "
        f"{' and '.join(missing_steps)} were dry-run; treat this as review-only until fresh deterministic execution runs."
    )
    findings = orchestrator_result.setdefault("quality_findings", [])
    if finding not in findings:
        findings.append(finding)
    orchestrator_result["status"] = "needs_review"


def unique(values: list[str]) -> list[str]:
    seen = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def clean_generated_run_artifacts(repo_root: Path, run_id: str) -> None:
    run_dir = repo_root / "agents" / "runs" / run_id
    if not run_dir.exists():
        return
    allowed_parent = (repo_root / "agents" / "runs").resolve()
    resolved_run_dir = run_dir.resolve()
    if resolved_run_dir.parent != allowed_parent:
        raise ValueError(f"Refusing to clean unexpected run directory: {run_dir}")

    for dirname in ("evidence_packets", "raw", "reports"):
        target = run_dir / dirname
        if target.exists():
            safe_remove_tree(target, resolved_run_dir)

    for filename in GENERATED_RUN_ROOT_FILES:
        target = run_dir / filename
        if target.exists():
            safe_remove_file(target, resolved_run_dir)


GENERATED_RUN_ROOT_FILES = (
    "run_summary.json",
    "run_summary.md",
    "quality_report.json",
    "quality_report.md",
    "finalization.json",
    "finalization.md",
    "memory_reflection.json",
    "memory_reflection.md",
    "memory_update_drafts.json",
    "memory_update_drafts.md",
    "memory_writer_prompt.json",
    "memory_writer_prompt.md",
    "memory_writer_review.json",
    "memory_writer_review.md",
    "agent_runtime_main_orchestrator.json",
    "agent_runtime_main_orchestrator.md",
    "orchestrator_update_proposals.md",
    "trace_links.md",
    "run_metrics.md",
    "orchestration_report.json",
    "orchestration_report.md",
)


def safe_remove_tree(path: Path, resolved_run_dir: Path) -> None:
    resolved = path.resolve()
    if resolved_run_dir not in resolved.parents:
        raise ValueError(f"Refusing to remove path outside run directory: {path}")
    shutil.rmtree(resolved)


def safe_remove_file(path: Path, resolved_run_dir: Path) -> None:
    resolved = path.resolve()
    if resolved_run_dir not in resolved.parents:
        raise ValueError(f"Refusing to remove path outside run directory: {path}")
    resolved.unlink()


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
        f"- agent_orchestrator: {result.steps['agent_orchestrator'].get('status', 'not_run')}",
        f"- orchestrator_proposal_review: {result.steps['orchestrator_proposal_review'].get('status', 'not_run')}",
        "",
        "## SDK Quality Findings",
        "",
    ]
    sdk_findings = result.steps["agent_orchestrator"].get("quality_findings", [])
    if sdk_findings:
        for finding in sdk_findings:
            lines.append(f"- {finding}")
    else:
        lines.append("- None.")
    lines.extend([
        "",
        "## Artifacts",
        "",
    ])
    if result.artifacts:
        for artifact in result.artifacts:
            lines.append(f"- `{artifact}`")
    else:
        lines.append("- No artifacts written.")
    lines.extend(["", "## Next Actions", ""])
    for action in result.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"
