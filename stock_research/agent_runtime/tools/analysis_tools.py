from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from agents import RunContextWrapper, function_tool

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.analysis_runner import AnalysisExecutor, run_analysis_tasks
from stock_research.provider_runner import read_manifest


def manifest_path_for_context(context: ResearchRunContext) -> Path:
    return context.manifest_path or context.run_dir / "manifest.json"


def relative_to_root(context: ResearchRunContext, path: Path) -> str:
    try:
        return path.relative_to(context.root).as_posix()
    except ValueError:
        return str(path)


def normalize_filter(value: str) -> set[str] | None:
    normalized = value.strip()
    return {normalized} if normalized else None


def normalize_limit(value: int) -> int | None:
    return value if value > 0 else None


def status_for_analysis_result(result: dict[str, Any]) -> str:
    if result.get("mode") == "dry_run":
        return "planned"
    if result.get("errors") or result.get("skipped"):
        return "needs_review"
    return "executed"


def run_analysis_tasks_for_context(
    context: ResearchRunContext,
    *,
    tool: str = "",
    task_id: str = "",
    limit: int = 0,
    execute: bool = False,
    current_date: date | None = None,
    executor: AnalysisExecutor | None = None,
) -> dict[str, Any]:
    manifest_path = manifest_path_for_context(context)
    if not manifest_path.exists():
        return {
            "status": "blocked",
            "reason": "manifest_not_found",
            "manifest_path": relative_to_root(context, manifest_path),
            "mode": "blocked",
        }

    if execute and (context.dry_run or not context.execute_analysis):
        return {
            "status": "blocked",
            "reason": "analysis_execution_not_permitted",
            "manifest_path": relative_to_root(context, manifest_path),
            "mode": "blocked",
            "requested_execute": True,
            "context_dry_run": context.dry_run,
            "execute_analysis": context.execute_analysis,
        }

    manifest = read_manifest(manifest_path)
    result = run_analysis_tasks(
        root=context.root,
        manifest=manifest,
        execute=execute,
        tools=normalize_filter(tool),
        task_ids=normalize_filter(task_id),
        limit=normalize_limit(limit),
        current_date=current_date,
        executor=executor,
    )
    return {
        "status": status_for_analysis_result(result),
        "manifest_path": relative_to_root(context, manifest_path),
        "filters": {
            "tool": tool.strip(),
            "task_id": task_id.strip(),
            "limit": normalize_limit(limit),
        },
        **result,
    }


@function_tool
def run_analysis_tasks_guarded(
    ctx: RunContextWrapper[ResearchRunContext],
    tool: str = "",
    task_id: str = "",
    limit: int = 0,
    execute: bool = False,
) -> str:
    """Plan or run manifest analysis tasks with dry-run-by-default permission checks."""
    return json.dumps(
        run_analysis_tasks_for_context(
            ctx.context,
            tool=tool,
            task_id=task_id,
            limit=limit,
            execute=execute,
        ),
        indent=2,
        sort_keys=True,
    )


def analysis_tools() -> list[Any]:
    return [run_analysis_tasks_guarded]
