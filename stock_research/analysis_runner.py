from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Callable

from .financial_compare import build_financial_compare_packet
from .financial_specialist import build_financial_specialist_packet


AnalysisExecutor = Callable[[Path, dict[str, Any], date | None], dict[str, Any]]


def run_analysis_tasks(
    root: Path,
    manifest: dict[str, Any],
    execute: bool = False,
    tools: set[str] | None = None,
    task_ids: set[str] | None = None,
    limit: int | None = None,
    current_date: date | None = None,
    executor: AnalysisExecutor | None = None,
) -> dict[str, Any]:
    tasks = order_analysis_tasks(selected_analysis_tasks(manifest.get("analysis_tasks", []), tools, task_ids, limit))
    selected_ids = {task.get("id", "") for task in tasks}
    successful_ids: set[str] = set()
    failed_ids: set[str] = set()
    result: dict[str, Any] = {
        "mode": "execute" if execute else "dry_run",
        "manifest_id": manifest.get("manifest_id", ""),
        "planned_count": len(tasks),
        "planned": [],
        "executed": [],
        "skipped": [],
        "errors": [],
    }

    for task in tasks:
        summary = summarize_analysis_task(task)
        if not execute:
            result["planned"].append(summary)
            continue

        blocked_by = blocking_dependencies(task, selected_ids, successful_ids, failed_ids)
        if blocked_by:
            failed_ids.add(task.get("id", ""))
            result["skipped"].append({**summary, "blocked_by": blocked_by})
            continue

        try:
            task_executor = executor or execute_analysis_task
            task_result = task_executor(root, task, current_date)
            successful_ids.add(task.get("id", ""))
            result["executed"].append({**summary, **task_result})
        except Exception as exc:
            failed_ids.add(task.get("id", ""))
            result["errors"].append({**summary, "error": str(exc)})

    return result


def selected_analysis_tasks(
    tasks: list[dict[str, Any]],
    tools: set[str] | None = None,
    task_ids: set[str] | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for task in tasks:
        if tools and task.get("tool") not in tools:
            continue
        if task_ids and task.get("id") not in task_ids:
            continue
        selected.append(task)
        if limit is not None and len(selected) >= limit:
            break
    return selected


def order_analysis_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    remaining = list(tasks)
    ordered: list[dict[str, Any]] = []
    selected_ids = {task.get("id", "") for task in tasks}
    emitted: set[str] = set()

    while remaining:
        progressed = False
        next_remaining: list[dict[str, Any]] = []
        for task in remaining:
            deps = [dep for dep in task.get("depends_on", []) if dep in selected_ids]
            if all(dep in emitted for dep in deps):
                ordered.append(task)
                emitted.add(task.get("id", ""))
                progressed = True
            else:
                next_remaining.append(task)
        if not progressed:
            ordered.extend(next_remaining)
            break
        remaining = next_remaining
    return ordered


def summarize_analysis_task(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": task.get("id", ""),
        "tool": task.get("tool", ""),
        "subject_type": task.get("subject_type", ""),
        "subject_id": task.get("subject_id", ""),
        "priority": task.get("priority", ""),
        "args": task.get("args", {}),
        "depends_on": task.get("depends_on", []),
        "reason": task.get("reason", ""),
    }


def blocking_dependencies(
    task: dict[str, Any],
    selected_ids: set[str],
    successful_ids: set[str],
    failed_ids: set[str],
) -> list[str]:
    blocked: list[str] = []
    for dependency in task.get("depends_on", []):
        if dependency not in selected_ids:
            continue
        if dependency in failed_ids or dependency not in successful_ids:
            blocked.append(dependency)
    return blocked


def execute_analysis_task(root: Path, task: dict[str, Any], current_date: date | None = None) -> dict[str, Any]:
    tool = task.get("tool", "")
    args = task.get("args", {})

    if tool == "financial_compare":
        packet, paths = build_financial_compare_packet(
            ticker=str(args["ticker"]),
            run_id=str(args["run_id"]),
            root=root,
            current_date=current_date,
            packet_paths=[Path(path) for path in args.get("packet_paths", [])] or None,
        )
        return analysis_result(packet.packet_id, paths)

    if tool == "financial_review":
        packet_path = args.get("financial_compare_packet")
        result = build_financial_specialist_packet(
            ticker=str(args["ticker"]),
            run_id=str(args["run_id"]),
            root=root,
            current_date=current_date,
            financial_compare_packet_path=Path(packet_path) if packet_path else None,
        )
        return {**analysis_result(result.packet.packet_id, result.paths), "review_status": result.review["status"]}

    raise ValueError(f"Unsupported analysis task tool={tool}")


def analysis_result(packet_id: str, paths: list[Path]) -> dict[str, Any]:
    return {"packet_id": packet_id, "paths": [str(path) for path in paths]}
