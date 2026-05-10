from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from agents import RunContextWrapper, function_tool

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.provider_runner import ProviderExecutor, read_manifest, run_provider_tasks


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


def status_for_provider_result(result: dict[str, Any]) -> str:
    if result.get("mode") == "dry_run":
        return "planned"
    if result.get("errors"):
        return "needs_review"
    return "executed"


def run_provider_tasks_for_context(
    context: ResearchRunContext,
    *,
    provider: str = "",
    task_id: str = "",
    limit: int = 0,
    execute: bool = False,
    current_date: date | None = None,
    executor: ProviderExecutor | None = None,
) -> dict[str, Any]:
    manifest_path = manifest_path_for_context(context)
    if not manifest_path.exists():
        return {
            "status": "blocked",
            "reason": "manifest_not_found",
            "manifest_path": relative_to_root(context, manifest_path),
            "mode": "blocked",
        }

    if execute and (context.dry_run or not context.execute_providers):
        return {
            "status": "blocked",
            "reason": "provider_execution_not_permitted",
            "manifest_path": relative_to_root(context, manifest_path),
            "mode": "blocked",
            "requested_execute": True,
            "context_dry_run": context.dry_run,
            "execute_providers": context.execute_providers,
        }

    manifest = read_manifest(manifest_path)
    result = run_provider_tasks(
        root=context.root,
        manifest=manifest,
        execute=execute,
        providers=normalize_filter(provider),
        task_ids=normalize_filter(task_id),
        limit=normalize_limit(limit),
        current_date=current_date,
        executor=executor,
    )
    return {
        "status": status_for_provider_result(result),
        "manifest_path": relative_to_root(context, manifest_path),
        "filters": {
            "provider": provider.strip(),
            "task_id": task_id.strip(),
            "limit": normalize_limit(limit),
        },
        **result,
    }


@function_tool
def run_provider_tasks_guarded(
    ctx: RunContextWrapper[ResearchRunContext],
    provider: str = "",
    task_id: str = "",
    limit: int = 0,
    execute: bool = False,
) -> str:
    """Plan or run manifest provider tasks with dry-run-by-default permission checks."""
    return json.dumps(
        run_provider_tasks_for_context(
            ctx.context,
            provider=provider,
            task_id=task_id,
            limit=limit,
            execute=execute,
        ),
        indent=2,
        sort_keys=True,
    )


def provider_tools() -> list[Any]:
    return [run_provider_tasks_guarded]
