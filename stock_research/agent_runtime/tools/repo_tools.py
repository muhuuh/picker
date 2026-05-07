from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents import RunContextWrapper, function_tool

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.memory import format_memory_context_for_prompt, load_memory_state


def safe_run_path(context: ResearchRunContext, name: str) -> Path:
    path = context.run_dir / name
    resolved = path.resolve()
    run_dir = context.run_dir.resolve()
    if resolved != run_dir and run_dir not in resolved.parents:
        raise ValueError(f"Path escapes run directory: {name}")
    return path


def safe_repo_path(context: ResearchRunContext, relative_path: str) -> Path:
    path = context.root / relative_path
    resolved = path.resolve()
    root = context.root.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"Path escapes repo root: {relative_path}")
    return path


def load_run_markdown_artifact(context: ResearchRunContext, artifact_name: str) -> str:
    if not artifact_name.endswith(".md"):
        raise ValueError("Only markdown run artifacts can be loaded by this tool.")
    path = safe_run_path(context, artifact_name)
    if not path.exists():
        return f"Missing run artifact: {artifact_name}"
    return path.read_text(encoding="utf-8")


def list_run_markdown_artifacts_data(context: ResearchRunContext) -> dict[str, Any]:
    run_dir = context.run_dir
    if not run_dir.exists():
        return {"run_id": context.run_id, "artifacts": []}
    artifacts = sorted(str(path.relative_to(run_dir)).replace("\\", "/") for path in run_dir.rglob("*.md"))
    return {"run_id": context.run_id, "artifacts": artifacts}


def load_repo_markdown_artifact(context: ResearchRunContext, relative_path: str) -> str:
    if not relative_path.endswith(".md"):
        raise ValueError("Only markdown repo artifacts can be loaded by this tool.")
    path = safe_repo_path(context, relative_path)
    if not path.exists():
        return f"Missing repo artifact: {relative_path}"
    return path.read_text(encoding="utf-8")


def load_memory_prompt_context_for_task(context: ResearchRunContext, task: str = "") -> str:
    requested_task = task.strip() or context.task
    if requested_task == context.task:
        return context.memory_context
    memory_state = load_memory_state(context.root)
    return format_memory_context_for_prompt(memory_state, requested_task)


def list_evidence_packets_data(context: ResearchRunContext) -> dict[str, Any]:
    evidence_dir = context.run_dir / "evidence_packets"
    if not evidence_dir.exists():
        return {"run_id": context.run_id, "evidence_packets": []}
    packets: list[dict[str, Any]] = []
    for path in sorted(evidence_dir.glob("*.json")):
        item: dict[str, Any] = {"path": str(path.relative_to(context.run_dir)).replace("\\", "/")}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            item["error"] = "invalid_json"
        else:
            item.update(
                {
                    "packet_id": data.get("packet_id", ""),
                    "provider": data.get("provider", ""),
                    "subject_type": data.get("subject", {}).get("type", "") if isinstance(data.get("subject"), dict) else "",
                    "subject_id": data.get("subject", {}).get("id", "") if isinstance(data.get("subject"), dict) else "",
                    "created_at": data.get("created_at", ""),
                }
            )
        packets.append(item)
    return {"run_id": context.run_id, "evidence_packets": packets}


@function_tool
def load_run_markdown(ctx: RunContextWrapper[ResearchRunContext], artifact_name: str) -> str:
    """Load a markdown artifact from the current run directory by relative path."""
    return load_run_markdown_artifact(ctx.context, artifact_name)


@function_tool
def list_run_markdown_artifacts(ctx: RunContextWrapper[ResearchRunContext]) -> str:
    """List markdown artifacts available under the current run directory."""
    return json.dumps(list_run_markdown_artifacts_data(ctx.context), indent=2)


@function_tool
def load_operational_memory(ctx: RunContextWrapper[ResearchRunContext]) -> str:
    """Load the task-relevant operational memory context already prepared for this run."""
    return ctx.context.memory_context


@function_tool
def load_memory_prompt_context(ctx: RunContextWrapper[ResearchRunContext], task: str = "") -> str:
    """Load prompt-ready operational memory for this task or another named task."""
    return load_memory_prompt_context_for_task(ctx.context, task)


@function_tool
def load_repo_map(ctx: RunContextWrapper[ResearchRunContext]) -> str:
    """Load docs/descriptions/repo_map.md from the repo."""
    return load_repo_markdown_artifact(ctx.context, "docs/descriptions/repo_map.md")


@function_tool
def load_run_summary(ctx: RunContextWrapper[ResearchRunContext]) -> str:
    """Load run_summary.md from the current run directory."""
    return load_run_markdown_artifact(ctx.context, "run_summary.md")


@function_tool
def load_quality_report(ctx: RunContextWrapper[ResearchRunContext]) -> str:
    """Load quality_report.md from the current run directory."""
    return load_run_markdown_artifact(ctx.context, "quality_report.md")


@function_tool
def list_evidence_packets(ctx: RunContextWrapper[ResearchRunContext]) -> str:
    """List provider-neutral evidence packets for the current run without loading raw payloads."""
    return json.dumps(list_evidence_packets_data(ctx.context), indent=2, sort_keys=True)


@function_tool
def load_stock_tracking_csv(ctx: RunContextWrapper[ResearchRunContext], category: str) -> str:
    """Load a stock tracking CSV: current_holdings, monitoring, or rejected."""
    allowed = {
        "current_holdings": "stock_tracking/current_holdings/current_holdings.csv",
        "monitoring": "stock_tracking/monitoring/monitoring.csv",
        "rejected": "stock_tracking/rejected/rejected.csv",
    }
    if category not in allowed:
        raise ValueError("category must be current_holdings, monitoring, or rejected")
    path = ctx.context.root / allowed[category]
    if not path.exists():
        return f"Missing stock tracking CSV: {allowed[category]}"
    return path.read_text(encoding="utf-8")


def repo_tools() -> list[Any]:
    return [
        load_run_markdown,
        list_run_markdown_artifacts,
        load_operational_memory,
        load_memory_prompt_context,
        load_repo_map,
        load_run_summary,
        load_quality_report,
        list_evidence_packets,
        load_stock_tracking_csv,
    ]
