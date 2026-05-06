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
    """Load a markdown artifact from the current run directory by file name."""
    if not artifact_name.endswith(".md"):
        raise ValueError("Only markdown run artifacts can be loaded by this tool.")
    path = _safe_run_path(ctx.context, artifact_name)
    if not path.exists():
        return f"Missing run artifact: {artifact_name}"
    return path.read_text(encoding="utf-8")


@function_tool
def list_run_markdown_artifacts(ctx: RunContextWrapper[ResearchRunContext]) -> str:
    """List markdown artifacts available in the current run directory."""
    run_dir = ctx.context.run_dir
    if not run_dir.exists():
        return json.dumps({"run_id": ctx.context.run_id, "artifacts": []})
    artifacts = sorted(str(path.relative_to(ctx.context.root)) for path in run_dir.glob("*.md"))
    return json.dumps({"run_id": ctx.context.run_id, "artifacts": artifacts}, indent=2)


@function_tool
def load_operational_memory(ctx: RunContextWrapper[ResearchRunContext]) -> str:
    """Load the task-relevant operational memory context already prepared for this run."""
    return ctx.context.memory_context


def repo_tools() -> list[Any]:
    return [load_run_markdown, list_run_markdown_artifacts, load_operational_memory]
