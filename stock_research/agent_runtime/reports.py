from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
from typing import Any

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.outputs import MainOrchestratorInputPacket
from stock_research.memory import relative_to_root
from stock_research.repo import load_first_table


def output_to_dict(output: Any) -> dict[str, Any]:
    if is_dataclass(output):
        return asdict(output)
    if hasattr(output, "model_dump"):
        return output.model_dump()
    if isinstance(output, dict):
        return output
    return {"value": str(output)}


def output_status(output: Any) -> str:
    data = output_to_dict(output)
    return str(data.get("status", "unknown"))


def build_orchestrator_input(
    run_id: str,
    memory_item_ids: tuple[str, ...] = (),
    provider_mode: str = "",
    analysis_mode: str = "",
    context: ResearchRunContext | None = None,
) -> str:
    memory_lines = []
    if memory_item_ids:
        memory_lines = [
            "",
            "Valid operational memory ids for this task include:",
            *[f"- {item_id}" for item_id in memory_item_ids[:20]],
        ]
    execution_lines = []
    if provider_mode or analysis_mode:
        execution_lines = [
            "",
            "Current scheduled execution modes:",
            f"- provider_tasks: {provider_mode or 'unknown'}",
            f"- analysis_tasks: {analysis_mode or 'unknown'}",
            "If provider_tasks or analysis_tasks are dry_run, treat the synthesis as based on existing artifacts, not a fresh current-cycle research execution.",
            "Do not claim the current run executed fresh provider or analysis work when those modes are dry_run.",
            "If fresh evidence is required for a proposed company-file update, mark the output partial or needs_human_review and add a next_run_task to execute the missing deterministic step.",
        ]
    packet_lines: list[str] = []
    if context:
        packet = build_main_orchestrator_input_packet(context, provider_mode=provider_mode, analysis_mode=analysis_mode)
        packet_lines = [
            "",
            "Main aggregation packet:",
            "```json",
            json.dumps(asdict(packet), indent=2, sort_keys=True),
            "```",
        ]
    return "\n".join(
        [
            f"Review stock research run `{run_id}`.",
            "",
            "Use the available repo/run inspection tools before deciding.",
            "Start by loading the repo map, listing markdown artifacts, and listing evidence packets. Then inspect the aggregate packet and at least:",
            "- run_summary.md",
            "- quality_report.md",
            "- finalization.md",
            "- company_research/*.md when present",
            "- market_research/*.md when present",
            "- portfolio_review/*.md when present",
            "- memory_evaluation/*.md when present",
            "- candidate verification result reports when present",
            "",
            "Also load the monitoring stock tracking CSV before proposing target files.",
            "Use the exact `stock_info_file` path from the CSV for company-file update proposals.",
            "",
            "Operational memory is mandatory context. Load task-relevant memory when needed and record the memory ids that materially shaped the decision.",
            "If deterministic-first workflow and registry composition shaped the decision, include their memory ids.",
            *execution_lines,
            *memory_lines,
            *packet_lines,
            "",
            "Return a structured OrchestratorDecision.",
            "Do not invent missing facts. If the evidence is too thin, set status to partial or needs_human_review.",
        ]
    )


def build_main_orchestrator_input_packet(
    context: ResearchRunContext,
    provider_mode: str = "",
    analysis_mode: str = "",
) -> MainOrchestratorInputPacket:
    return MainOrchestratorInputPacket(
        run_id=context.run_id,
        provider_mode=provider_mode,
        analysis_mode=analysis_mode,
        run_artifacts=existing_relative_paths(
            context,
            [
                context.run_dir / "run_summary.md",
                context.run_dir / "quality_report.md",
                context.run_dir / "finalization.md",
                context.run_dir / "orchestration_report.md",
                context.run_dir / "agent_runtime_main_orchestrator.md",
                context.run_dir / "trace_links.md",
                context.run_dir / "run_metrics.md",
            ],
        ),
        company_research_reports=relative_glob(context, "company_research/*.md"),
        market_research_reports=relative_glob(context, "market_research/*.md"),
        portfolio_review_reports=relative_glob(context, "portfolio_review/*.md"),
        memory_evaluation_reports=relative_glob(context, "memory_evaluation/*.md"),
        candidate_verification_results=relative_glob(context, "market_research/candidate_verification_result.md"),
        human_review_digest=relative_path_if_exists(context, context.root / "agents" / "human_review_digest.md"),
        open_human_review_count=count_human_review_rows(context, {"open", "needs_more_research"}),
        approved_human_review_count=count_human_review_rows(context, {"approved"}),
        memory_item_ids=list(context.memory_item_ids),
    )


def relative_glob(context: ResearchRunContext, pattern: str) -> list[str]:
    return [
        relative_to_root(context.root, path).as_posix()
        for path in sorted(context.run_dir.glob(pattern))
        if path.is_file()
    ]


def existing_relative_paths(context: ResearchRunContext, paths: list[Path]) -> list[str]:
    return [relative_to_root(context.root, path).as_posix() for path in paths if path.exists()]


def relative_path_if_exists(context: ResearchRunContext, path: Path) -> str:
    return relative_to_root(context.root, path).as_posix() if path.exists() else ""


def count_human_review_rows(context: ResearchRunContext, statuses: set[str]) -> int:
    rows = load_first_table(context.root / "agents" / "human_review_queue.md")
    return sum(1 for row in rows if str(row.get("Status", "")).lower() in statuses)


def write_agent_runtime_report(context: ResearchRunContext, agent_id: str, output: Any) -> tuple[Path, Path]:
    context.run_dir.mkdir(parents=True, exist_ok=True)
    data = output_to_dict(output)
    json_path = context.run_dir / f"agent_runtime_{agent_id}.json"
    md_path = context.run_dir / f"agent_runtime_{agent_id}.md"
    json_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(format_agent_runtime_markdown(context, agent_id, data), encoding="utf-8")
    return json_path, md_path


def format_agent_runtime_markdown(context: ResearchRunContext, agent_id: str, data: dict[str, Any]) -> str:
    lines = [
        f"# Agent Runtime Report: {agent_id}",
        "",
        f"- run_id: {context.run_id}",
        f"- trace_id: {context.trace_id}",
        f"- group_id: {context.trace_group_id}",
        f"- status: {data.get('status', 'unknown')}",
        "",
        "## Summary",
        "",
        str(data.get("summary", "") or "No summary returned."),
        "",
    ]
    for section, title in (
        ("alerts", "Alerts"),
        ("file_update_proposals", "File Update Proposals"),
        ("human_review_items", "Human Review Items"),
        ("next_run_tasks", "Next Run Tasks"),
        ("memory_item_ids_used", "Memory Items Used"),
    ):
        values = data.get(section) or []
        lines.extend([f"## {title}", ""])
        if not values:
            lines.append("- None.")
        else:
            for value in values:
                if isinstance(value, dict):
                    label = value.get("title") or value.get("summary") or value.get("question") or json.dumps(value, sort_keys=True)
                    lines.append(f"- {label}")
                else:
                    lines.append(f"- {value}")
        lines.append("")
    return "\n".join(lines)


def evaluate_runtime_output_quality(output: Any, context: ResearchRunContext | None = None) -> list[str]:
    data = output_to_dict(output)
    findings: list[str] = []
    source_ids = collect_source_ids(data)
    summary = str(data.get("summary", "")).strip()
    if len(summary) < 80:
        findings.append("Summary is too short for useful review.")
    if data.get("status") not in {"ready", "partial", "needs_human_review", "blocked"}:
        findings.append("Status is missing or invalid.")
    if "buy" in summary.lower() or "sell" in summary.lower():
        findings.append("Summary may contain direct trade language; recommendations should remain review items.")
    validate_memory_ids(data, context, findings, "top-level output")
    validate_sources(data, context, findings, "top-level output")
    for index, specialist_result in enumerate(data.get("specialist_results") or []):
        if isinstance(specialist_result, dict):
            validate_memory_ids(specialist_result, context, findings, f"specialist_results[{index}]")
            validate_sources(specialist_result, context, findings, f"specialist_results[{index}]")
            validate_file_update_proposals(
                specialist_result.get("file_update_proposals") or [],
                context,
                findings,
                source_ids,
                f"specialist_results[{index}]",
            )
    validate_file_update_proposals(data.get("file_update_proposals") or [], context, findings, source_ids, "top-level output")
    validate_candidate_leads(data.get("candidate_leads") or [], findings, "top-level output")
    return findings


def collect_source_ids(data: dict[str, Any]) -> set[str]:
    source_ids: set[str] = set()
    for source in data.get("sources") or []:
        if isinstance(source, dict) and source.get("source_id"):
            source_ids.add(str(source["source_id"]))
    for specialist_result in data.get("specialist_results") or []:
        if not isinstance(specialist_result, dict):
            continue
        for source in specialist_result.get("sources") or []:
            if isinstance(source, dict) and source.get("source_id"):
                source_ids.add(str(source["source_id"]))
    return source_ids


def validate_file_update_proposals(
    proposals: list[Any],
    context: ResearchRunContext | None,
    findings: list[str],
    source_ids: set[str],
    label: str,
) -> None:
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        target_file = str(proposal.get("target_file", "")).strip()
        if not target_file:
            findings.append(f"{label} has a file update proposal missing target_file.")
            continue
        if context:
            target_path = context.root / target_file
            if not target_path.exists():
                findings.append(f"{label} file update proposal target does not exist: {target_file}")
        proposal_source_ids = [str(source_id) for source_id in proposal.get("source_ids") or []]
        if not proposal_source_ids:
            findings.append(f"{label} file update proposal for {target_file} has no source_ids.")
        missing_source_ids = [source_id for source_id in proposal_source_ids if source_id not in source_ids]
        if missing_source_ids:
            findings.append(
                f"{label} file update proposal for {target_file} references unknown source_ids: {', '.join(missing_source_ids)}"
            )


def validate_memory_ids(data: dict[str, Any], context: ResearchRunContext | None, findings: list[str], label: str) -> None:
    if not data.get("memory_item_ids_used"):
        findings.append(f"{label} did not record operational memory item ids used.")
    elif context:
        known_ids = set(context.known_memory_item_ids or context.memory_item_ids)
        invalid_ids = [item_id for item_id in data.get("memory_item_ids_used", []) if item_id not in known_ids]
        if invalid_ids:
            findings.append(f"{label} recorded unknown operational memory item ids: {', '.join(invalid_ids)}")


def validate_sources(
    data: dict[str, Any],
    context: ResearchRunContext | None,
    findings: list[str],
    label: str,
) -> None:
    for index, source in enumerate(data.get("sources") or []):
        if not isinstance(source, dict):
            continue
        source_id = str(source.get("source_id", "")).strip()
        url = str(source.get("url", "")).strip()
        artifact_path = str(source.get("artifact_path", "")).strip()
        if not source_id:
            findings.append(f"{label} source[{index}] is missing source_id.")
        if not url and not artifact_path:
            findings.append(f"{label} source[{index}] has neither url nor artifact_path.")
        if artifact_path and context:
            normalized = artifact_path.replace("\\", "/")
            candidates = [
                context.run_dir / normalized,
                context.root / normalized,
            ]
            if not any(candidate.exists() for candidate in candidates):
                findings.append(f"{label} source[{index}] artifact_path does not exist: {artifact_path}")


def validate_candidate_leads(candidate_leads: list[Any], findings: list[str], label: str) -> None:
    for index, lead in enumerate(candidate_leads):
        if not isinstance(lead, dict):
            findings.append(f"{label} candidate_leads[{index}] is not an object.")
            continue
        candidate_label = str(lead.get("ticker") or lead.get("company_name") or f"candidate_leads[{index}]")
        source_ids = [str(source_id) for source_id in lead.get("source_ids") or []]
        verification_status = str(lead.get("verification_status", "")).strip()
        next_action = str(lead.get("next_action", "")).strip()
        cooldown_status = str(lead.get("rejected_cooldown_status", "")).strip()
        if not source_ids:
            findings.append(f"{label} candidate lead {candidate_label} has no source_ids.")
        if not verification_status:
            findings.append(f"{label} candidate lead {candidate_label} has no verification_status.")
        if verification_status == "grok_only" and next_action == "add_to_monitoring":
            findings.append(f"{label} candidate lead {candidate_label} is Grok-only but marked for monitoring.")
        if cooldown_status == "cooldown_active" and next_action == "add_to_monitoring":
            findings.append(f"{label} candidate lead {candidate_label} is still in rejected cooldown but marked for monitoring.")
        if bool(lead.get("rumor_flag")) and verification_status == "verified" and next_action == "add_to_monitoring":
            findings.append(f"{label} candidate lead {candidate_label} is rumor-flagged but marked as verified promotion.")
