from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents import RunContextWrapper, function_tool

from stock_research.agent_runtime.context import ResearchRunContext


def _safe_run_path(context: ResearchRunContext, name: str) -> Path:
    path = context.run_dir / name
    resolved = path.resolve()
    run_dir = context.run_dir.resolve()
    if resolved != run_dir and run_dir not in resolved.parents:
        raise ValueError(f"Path escapes run directory: {name}")
    return path


@function_tool
def load_run_markdown(ctx: RunContextWrapper[ResearchRunContext], artifact_name: str) -> str:
    """Load a markdown artifact from the current run directory by relative path."""
    if not artifact_name.endswith(".md"):
        raise ValueError("Only markdown run artifacts can be loaded by this tool.")
    path = _safe_run_path(ctx.context, artifact_name)
    if not path.exists():
        return f"Missing run artifact: {artifact_name}"
    return path.read_text(encoding="utf-8")


@function_tool
def list_run_markdown_artifacts(ctx: RunContextWrapper[ResearchRunContext]) -> str:
    """List markdown artifacts available under the current run directory."""
    run_dir = ctx.context.run_dir
    if not run_dir.exists():
        return json.dumps({"run_id": ctx.context.run_id, "artifacts": []})
    artifacts = sorted(str(path.relative_to(run_dir)) for path in run_dir.rglob("*.md"))
    return json.dumps({"run_id": ctx.context.run_id, "artifacts": artifacts}, indent=2)


@function_tool
def load_operational_memory(ctx: RunContextWrapper[ResearchRunContext]) -> str:
    """Load the task-relevant operational memory context already prepared for this run."""
    return ctx.context.memory_context


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
    return [load_run_markdown, list_run_markdown_artifacts, load_operational_memory, load_stock_tracking_csv]
