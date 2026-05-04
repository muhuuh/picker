from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Callable

from .config import get_config_value
from .providers.alpha_vantage import AlphaVantageCompanyOptions, build_alpha_vantage_company_packet, resolve_alpha_vantage_api_key
from .providers.exa import ExaContentsOptions, ExaSearchOptions, build_exa_contents_packet, build_exa_search_packet, resolve_exa_api_key
from .providers.fmp import FmpCompanyOptions, build_fmp_company_packet, resolve_fmp_api_key
from .providers.polygon_provider import PolygonCompanyOptions, build_polygon_company_packet, resolve_polygon_api_key
from .providers.sec_edgar import build_sec_company_packet, resolve_sec_user_agent
from .providers.xai_grok import XaiXSearchOptions, build_xai_x_search_packet, resolve_xai_api_key
from .providers.yfinance_provider import build_yfinance_company_packet


ProviderExecutor = Callable[[Path, dict[str, Any], date | None], dict[str, Any]]


def read_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_provider_tasks(
    root: Path,
    manifest: dict[str, Any],
    execute: bool = False,
    providers: set[str] | None = None,
    task_ids: set[str] | None = None,
    limit: int | None = None,
    current_date: date | None = None,
    executor: ProviderExecutor | None = None,
) -> dict[str, Any]:
    tasks = selected_provider_tasks(manifest.get("provider_tasks", []), providers, task_ids, limit)
    result: dict[str, Any] = {
        "mode": "execute" if execute else "dry_run",
        "manifest_id": manifest.get("manifest_id", ""),
        "planned_count": len(tasks),
        "planned": [],
        "executed": [],
        "errors": [],
    }

    for task in tasks:
        summary = summarize_provider_task(task)
        if not execute:
            result["planned"].append(summary)
            continue

        try:
            task_executor = executor or execute_provider_task
            task_result = task_executor(root, task, current_date)
            result["executed"].append({**summary, **task_result})
        except Exception as exc:
            result["errors"].append({**summary, "error": str(exc)})

    return result


def selected_provider_tasks(
    tasks: list[dict[str, Any]],
    providers: set[str] | None = None,
    task_ids: set[str] | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for task in tasks:
        if providers and task.get("provider") not in providers:
            continue
        if task_ids and task.get("id") not in task_ids:
            continue
        selected.append(task)
        if limit is not None and len(selected) >= limit:
            break
    return selected


def summarize_provider_task(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": task.get("id", ""),
        "provider": task.get("provider", ""),
        "tool": task.get("tool", ""),
        "subject_type": task.get("subject_type", ""),
        "subject_id": task.get("subject_id", ""),
        "priority": task.get("priority", ""),
        "args": task.get("args", {}),
        "reason": task.get("reason", ""),
    }


def execute_provider_task(root: Path, task: dict[str, Any], current_date: date | None = None) -> dict[str, Any]:
    provider = task.get("provider", "")
    tool = task.get("tool", "")
    args = task.get("args", {})

    if provider == "yfinance" and tool == "company":
        packet, paths = build_yfinance_company_packet(
            ticker=str(args["ticker"]),
            run_id=str(args["run_id"]),
            root=root,
            current_date=current_date,
            period=str(args.get("period", "5d")),
        )
        return packet_result(packet.packet_id, paths)

    if provider == "fmp" and tool == "company":
        api_key = resolve_fmp_api_key(
            get_config_value(root, "FMP_API_KEY") or get_config_value(root, "FINANCIAL_MODELING_PREP_API_KEY")
        )
        packet, paths = build_fmp_company_packet(
            options=FmpCompanyOptions(
                ticker=str(args["ticker"]),
                include_statements=bool(args.get("include_statements", False)),
            ),
            api_key=api_key,
            run_id=str(args["run_id"]),
            root=root,
            current_date=current_date,
        )
        return packet_result(packet.packet_id, paths)

    if provider == "polygon" and tool == "company":
        api_key = resolve_polygon_api_key(get_config_value(root, "POLYGON_API_KEY") or get_config_value(root, "MASSIVE_API_KEY"))
        packet, paths = build_polygon_company_packet(
            options=PolygonCompanyOptions(
                ticker=str(args["ticker"]),
                adjusted=bool(args.get("adjusted", True)),
            ),
            api_key=api_key,
            run_id=str(args["run_id"]),
            root=root,
            current_date=current_date,
        )
        return packet_result(packet.packet_id, paths)

    if provider == "alpha_vantage" and tool == "company":
        api_key = resolve_alpha_vantage_api_key(get_config_value(root, "ALPHA_VANTAGE_API_KEY"))
        packet, paths = build_alpha_vantage_company_packet(
            options=AlphaVantageCompanyOptions(
                ticker=str(args["ticker"]),
                include_statements=bool(args.get("include_statements", False)),
            ),
            api_key=api_key,
            run_id=str(args["run_id"]),
            root=root,
            current_date=current_date,
        )
        return packet_result(packet.packet_id, paths)

    if provider == "sec_edgar" and tool == "company":
        user_agent = resolve_sec_user_agent(
            get_config_value(root, "SEC_USER_AGENT") or get_config_value(root, "STOCK_RESEARCH_SEC_USER_AGENT")
        )
        packet, paths = build_sec_company_packet(
            ticker=str(args["ticker"]),
            user_agent=user_agent,
            run_id=str(args["run_id"]),
            root=root,
            include_facts=bool(args.get("include_facts", False)),
            current_date=current_date,
        )
        return packet_result(packet.packet_id, paths)

    if provider == "exa" and tool == "search":
        api_key = resolve_exa_api_key(get_config_value(root, "EXA_API_KEY"))
        packet, paths = build_exa_search_packet(
            options=ExaSearchOptions(
                query=str(args["query"]),
                subject_type=str(task["subject_type"]),
                subject_id=str(task["subject_id"]),
                search_mode=str(args.get("mode", "general")),
                search_type=str(args.get("type", "auto")),
                num_results=int(args.get("num_results", 10)),
                start_published_date=str(args.get("start_published_date", "")),
                end_published_date=str(args.get("end_published_date", "")),
                include_domains=tuple(args.get("include_domains", [])),
                exclude_domains=tuple(args.get("exclude_domains", [])),
                max_age_hours=args.get("max_age_hours"),
                artifact_id=str(task.get("id", "")),
            ),
            api_key=api_key,
            run_id=str(args["run_id"]),
            root=root,
            current_date=current_date,
        )
        return packet_result(packet.packet_id, paths)

    if provider == "exa" and tool == "contents":
        api_key = resolve_exa_api_key(get_config_value(root, "EXA_API_KEY"))
        urls = args.get("urls", args.get("url", []))
        if isinstance(urls, str):
            urls = [urls]
        packet, paths = build_exa_contents_packet(
            options=ExaContentsOptions(
                urls=tuple(str(url) for url in urls),
                subject_type=str(task["subject_type"]),
                subject_id=str(task["subject_id"]),
                highlights_query=str(args.get("highlights_query", "")),
                text_max_characters=args.get("text_max_characters"),
                max_age_hours=args.get("max_age_hours"),
                livecrawl_timeout=int(args.get("livecrawl_timeout", 12000)),
                artifact_id=str(task.get("id", "")),
            ),
            api_key=api_key,
            run_id=str(args["run_id"]),
            root=root,
            current_date=current_date,
        )
        return packet_result(packet.packet_id, paths)

    if provider == "xai_grok" and tool == "x_search":
        api_key = resolve_xai_api_key(get_config_value(root, "XAI_API_KEY"))
        packet, paths = build_xai_x_search_packet(
            options=XaiXSearchOptions(
                prompt=str(args["prompt"]),
                subject_type=str(task["subject_type"]),
                subject_id=str(task["subject_id"]),
                research_kind=str(args.get("research_kind", "x_sentiment")),
                model=str(args.get("model", "grok-4.3")),
                from_date=str(args.get("from_date", "")),
                to_date=str(args.get("to_date", "")),
                allowed_x_handles=tuple(args.get("allowed_x_handles", [])),
                excluded_x_handles=tuple(args.get("excluded_x_handles", [])),
                enable_image_understanding=bool(args.get("enable_image_understanding", False)),
                enable_video_understanding=bool(args.get("enable_video_understanding", False)),
                artifact_id=str(task.get("id", "")),
            ),
            api_key=api_key,
            run_id=str(args["run_id"]),
            root=root,
            current_date=current_date,
        )
        return packet_result(packet.packet_id, paths)

    raise ValueError(f"Unsupported provider task: provider={provider}, tool={tool}")


def packet_result(packet_id: str, paths: list[Path]) -> dict[str, Any]:
    return {"packet_id": packet_id, "paths": [str(path) for path in paths]}
