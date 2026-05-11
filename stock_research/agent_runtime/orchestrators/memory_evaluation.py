from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext, with_task_memory
from stock_research.agent_runtime.outputs import (
    MemoryEvaluationArtifact,
    MemoryEvaluationPacket,
    OrchestratorDecision,
)
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.reports import output_to_dict
from stock_research.agent_runtime.specialists.quality_review import build_agent as build_quality_review_agent
from stock_research.agent_runtime.tools.repo_tools import repo_tools
from stock_research.memory import relative_to_root
from stock_research.memory_reflection import build_run_reflection, read_json_if_exists, read_run_metrics


FALLBACK_PROMPT = """
You are the memory and evaluation sub-orchestrator.

Review run telemetry, quality reports, memory reflection, recurring failures, memory update drafts, and user-correction signals.
Your job is to decide whether the run's learning loop is healthy and what should be reviewed next.
Do not directly edit operational memory. Memory changes must stay proposal-first and go through deterministic draft/apply commands.
"""


def build_agent(context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    root = context.root if context else None
    prompt = FALLBACK_PROMPT if root is None else load_prompt(root, "agents/orchestrator/prompts/memory_evaluation.md", FALLBACK_PROMPT)
    if context:
        prompt = with_memory(prompt, context.memory_context)

    quality_context = with_task_memory(context, "quality reviewer specialist") if context else None
    quality_agent = build_quality_review_agent(quality_context)
    return Agent[ResearchRunContext](
        name="Memory Evaluation Orchestrator",
        instructions=prompt,
        handoff_description="Reviews run telemetry, memory reflection, update drafts, and learning-loop health.",
        output_type=OrchestratorDecision,
        tools=[
            *repo_tools(),
            quality_agent.as_tool(
                tool_name="quality_reviewer_specialist",
                tool_description="Review memory/evaluation output quality, missing telemetry, and learning-loop gates.",
            ),
        ],
    )


def build_memory_evaluation_packet(context: ResearchRunContext) -> MemoryEvaluationPacket:
    reflection = safe_build_reflection(context)
    recurring = read_json_if_exists(context.root / "agents" / "memory" / "recurring_failures.json")
    drafts = read_json_if_exists(context.run_dir / "memory_update_drafts.json")
    finalization = read_json_if_exists(context.run_dir / "finalization.json")
    metrics_rows = read_run_metrics(context.run_dir / "run_metrics.md")

    artifacts = collect_memory_evaluation_artifacts(context)
    reflection_issues = list(reflection.get("issues", []))
    reflection_proposals = list(reflection.get("memory_update_proposals", []))
    recurring_patterns = list(recurring.get("patterns", []))
    recurring_proposals = list(recurring.get("memory_update_proposals", []))
    draft_items = list(drafts.get("items", []))
    ready_drafts = [item for item in draft_items if str(item.get("status", "")) == "ready"]
    timeout_rows = [row for row in metrics_rows if row.get("status") == "timeout"]
    error_rows = [row for row in metrics_rows if row.get("status") == "error"]
    injected_memory_ids = sorted(unique_memory_ids(row for row in metrics_rows if str(row.get("metric", "")).startswith("memory_context:")))
    reported_memory_ids = sorted(unique_memory_ids(row for row in metrics_rows if str(row.get("metric", "")).startswith("memory_output:")))

    issues = summarize_issues(reflection_issues, timeout_rows, error_rows, artifacts)
    next_actions = build_next_actions(
        reflection_issues=reflection_issues,
        recurring_patterns=recurring_patterns,
        draft_items=draft_items,
        ready_drafts=ready_drafts,
        finalization=finalization,
        metrics_rows=metrics_rows,
        artifacts=artifacts,
    )
    status = packet_status(
        reflection_issues=reflection_issues,
        recurring_patterns=recurring_patterns,
        ready_drafts=ready_drafts,
        timeout_rows=timeout_rows,
        error_rows=error_rows,
        artifacts=artifacts,
    )

    return MemoryEvaluationPacket(
        run_id=context.run_id,
        status=status,
        reflection_issue_count=len(reflection_issues),
        recurring_pattern_count=len(recurring_patterns),
        memory_update_proposal_count=len(reflection_proposals) + len(recurring_proposals),
        memory_update_draft_count=len(draft_items),
        ready_memory_update_draft_count=len(ready_drafts),
        sdk_metric_rows=len(metrics_rows),
        sdk_timeout_count=len(timeout_rows),
        sdk_error_count=len(error_rows),
        injected_memory_ids=injected_memory_ids,
        reported_memory_ids=reported_memory_ids,
        artifacts=artifacts,
        issues=issues,
        next_actions=next_actions,
        memory_item_ids=list(context.memory_item_ids),
    )


def build_memory_evaluation_input(context: ResearchRunContext) -> str:
    packet = build_memory_evaluation_packet(context)
    return "\n".join(
        [
            f"Review memory/evaluation health for run `{packet.run_id}`.",
            "",
            "Use the memory evaluation packet below as the deterministic starting point.",
            "Focus on telemetry coverage, reflection issues, recurring failures, memory update drafts, and whether the run should create or apply operational-memory updates.",
            "Do not directly edit `agents/memory/*.md`; only propose reviewable next actions.",
            "",
            "Memory evaluation packet:",
            "```json",
            json.dumps(asdict(packet), indent=2, sort_keys=True),
            "```",
        ]
    )


def aggregate_memory_evaluation(context: ResearchRunContext) -> OrchestratorDecision:
    packet = build_memory_evaluation_packet(context)
    summary = (
        f"Memory evaluation found {packet.reflection_issue_count} reflection issue(s), "
        f"{packet.recurring_pattern_count} recurring pattern(s), "
        f"{packet.memory_update_draft_count} draft memory update(s), "
        f"and {packet.sdk_metric_rows} SDK metric row(s)."
    )
    return OrchestratorDecision(
        agent_id="memory_evaluation_orchestrator",
        run_id=context.run_id,
        status=packet.status,
        summary=summary,
        next_run_tasks=packet.next_actions,
        memory_item_ids_used=list(context.memory_item_ids),
    )


def write_memory_evaluation_report(context: ResearchRunContext, decision: OrchestratorDecision | None = None) -> tuple[Path, Path]:
    packet = build_memory_evaluation_packet(context)
    resolved_decision = decision or aggregate_memory_evaluation(context)
    target_dir = context.run_dir / "memory_evaluation"
    target_dir.mkdir(parents=True, exist_ok=True)
    json_path = target_dir / "memory_evaluation.json"
    md_path = target_dir / "memory_evaluation.md"
    json_path.write_text(
        json.dumps({"decision": output_to_dict(resolved_decision), "packet": asdict(packet)}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    md_path.write_text(format_memory_evaluation_markdown(packet, resolved_decision), encoding="utf-8")
    return json_path, md_path


def format_memory_evaluation_markdown(packet: MemoryEvaluationPacket, decision: OrchestratorDecision) -> str:
    lines = [
        f"# Memory Evaluation: {packet.run_id}",
        "",
        f"Status: {decision.status}",
        "",
        "## Summary",
        "",
        decision.summary,
        "",
        "## Metrics",
        "",
        f"- reflection issues: {packet.reflection_issue_count}",
        f"- recurring patterns: {packet.recurring_pattern_count}",
        f"- memory update proposals: {packet.memory_update_proposal_count}",
        f"- memory update drafts: {packet.memory_update_draft_count}",
        f"- ready memory update drafts: {packet.ready_memory_update_draft_count}",
        f"- SDK metric rows: {packet.sdk_metric_rows}",
        f"- SDK timeouts: {packet.sdk_timeout_count}",
        f"- SDK errors: {packet.sdk_error_count}",
        "",
        "## Artifacts",
        "",
        "| Type | Status | Path | Summary |",
        "| --- | --- | --- | --- |",
    ]
    for artifact in packet.artifacts:
        lines.append(
            "| "
            + " | ".join(
                escape_cell(value)
                for value in [artifact.artifact_type, artifact.status, artifact.path, artifact.summary]
            )
            + " |"
        )
    lines.extend(["", "## Issues", ""])
    if packet.issues:
        lines.extend(f"- {issue}" for issue in packet.issues)
    else:
        lines.append("- No memory/evaluation issues found.")
    lines.extend(["", "## Next Actions", ""])
    if packet.next_actions:
        lines.extend(f"- {action}" for action in packet.next_actions)
    else:
        lines.append("- None.")
    return "\n".join(lines).rstrip() + "\n"


def safe_build_reflection(context: ResearchRunContext) -> dict[str, Any]:
    existing = read_json_if_exists(context.run_dir / "memory_reflection.json")
    if existing:
        return existing
    if not context.run_dir.exists():
        return {"issues": [], "memory_update_proposals": [], "metrics": {}}
    try:
        reflection = build_run_reflection(context.root, context.run_id)
    except Exception as exc:  # noqa: BLE001 - evaluation should report rather than crash.
        return {
            "issues": [
                {
                    "severity": "high",
                    "category": "reflection_build_failed",
                    "summary": f"Could not build memory reflection: {exc}",
                    "evidence": relative_to_root(context.root, context.run_dir).as_posix(),
                }
            ],
            "memory_update_proposals": [],
            "metrics": {},
        }
    return {
        "issues": [asdict(issue) for issue in reflection.issues],
        "memory_update_proposals": [asdict(proposal) for proposal in reflection.memory_update_proposals],
        "metrics": reflection.metrics,
    }


def collect_memory_evaluation_artifacts(context: ResearchRunContext) -> list[MemoryEvaluationArtifact]:
    run_artifacts = [
        ("run_summary", context.run_dir / "run_summary.md", "summarizes deterministic run outputs"),
        ("quality_report", context.run_dir / "quality_report.md", "deterministic evidence/source quality report"),
        ("run_metrics", context.run_dir / "run_metrics.md", "local SDK telemetry"),
        ("memory_reflection", context.run_dir / "memory_reflection.md", "post-run memory reflection"),
        ("memory_update_drafts", context.run_dir / "memory_update_drafts.md", "schema-valid memory update drafts"),
        ("memory_writer_review", context.run_dir / "memory_writer_review.md", "bounded memory writer review"),
        ("finalization", context.run_dir / "finalization.md", "run finalization summary"),
    ]
    artifacts = [
        MemoryEvaluationArtifact(
            artifact_type=artifact_type,
            path=relative_to_root(context.root, path).as_posix(),
            status="present" if path.exists() else "missing",
            summary=summary,
        )
        for artifact_type, path, summary in run_artifacts
    ]
    recurring_path = context.root / "agents" / "memory" / "recurring_failures.md"
    artifacts.append(
        MemoryEvaluationArtifact(
            artifact_type="recurring_failures",
            path=relative_to_root(context.root, recurring_path).as_posix(),
            status="present" if recurring_path.exists() else "missing",
            summary="cross-run recurring failure report",
        )
    )
    return artifacts


def summarize_issues(
    reflection_issues: list[dict[str, Any]],
    timeout_rows: list[dict[str, Any]],
    error_rows: list[dict[str, Any]],
    artifacts: list[MemoryEvaluationArtifact],
) -> list[str]:
    issues: list[str] = []
    for issue in reflection_issues[:10]:
        issues.append(f"{issue.get('severity', 'unknown')} {issue.get('category', 'unknown')}: {issue.get('summary', '')}")
    for row in timeout_rows:
        issues.append(f"SDK timeout: {row.get('metric', '')} {row.get('detail', '')}".strip())
    for row in error_rows:
        issues.append(f"SDK error: {row.get('metric', '')} {row.get('detail', '')}".strip())
    missing_required = [
        artifact.artifact_type
        for artifact in artifacts
        if artifact.status == "missing" and artifact.artifact_type in {"run_summary", "quality_report", "memory_reflection", "finalization"}
    ]
    if missing_required:
        issues.append("Missing learning-loop artifact(s): " + ", ".join(missing_required) + ".")
    return issues


def build_next_actions(
    *,
    reflection_issues: list[dict[str, Any]],
    recurring_patterns: list[dict[str, Any]],
    draft_items: list[dict[str, Any]],
    ready_drafts: list[dict[str, Any]],
    finalization: dict[str, Any],
    metrics_rows: list[dict[str, Any]],
    artifacts: list[MemoryEvaluationArtifact],
) -> list[str]:
    actions: list[str] = []
    if any(artifact.artifact_type == "memory_reflection" and artifact.status == "missing" for artifact in artifacts):
        actions.append("Run deterministic memory finalization so reflection artifacts exist for this run.")
    if not metrics_rows and any(artifact.artifact_type == "run_metrics" and artifact.status == "missing" for artifact in artifacts):
        actions.append("Run SDK orchestration or accept that no SDK telemetry exists for this run.")
    if reflection_issues:
        actions.append("Review `memory_reflection.md` before treating the run as learning-loop complete.")
    if recurring_patterns:
        actions.append("Review `agents/memory/recurring_failures.md` for repeated workflow issues.")
    if draft_items:
        actions.append("Review `memory_update_drafts.md`; apply only approved ready drafts with `memory apply-updates`.")
    if ready_drafts:
        actions.append(f"{len(ready_drafts)} memory draft(s) are ready for approval/application.")
    if finalization and finalization.get("status") not in {"complete", ""}:
        actions.append("Resolve finalization next actions before accepting this run as complete.")
    if not actions:
        actions.append("No immediate learning-loop action required.")
    return unique(actions)


def packet_status(
    *,
    reflection_issues: list[dict[str, Any]],
    recurring_patterns: list[dict[str, Any]],
    ready_drafts: list[dict[str, Any]],
    timeout_rows: list[dict[str, Any]],
    error_rows: list[dict[str, Any]],
    artifacts: list[MemoryEvaluationArtifact],
) -> str:
    if timeout_rows or error_rows:
        return "blocked"
    if reflection_issues or recurring_patterns or ready_drafts:
        return "needs_human_review"
    missing_required = [
        artifact
        for artifact in artifacts
        if artifact.status == "missing" and artifact.artifact_type in {"run_summary", "quality_report", "memory_reflection", "finalization"}
    ]
    if missing_required:
        return "partial"
    return "ready"


def unique_memory_ids(rows) -> set[str]:
    ids: set[str] = set()
    for row in rows:
        for item in row.get("memory_item_ids", ()):
            if item:
                ids.add(str(item))
    return ids


def unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result


def escape_cell(value: Any) -> str:
    return str(value).replace("|", "/").replace("\n", " ").strip()
