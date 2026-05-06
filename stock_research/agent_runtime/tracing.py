from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from stock_research.agent_runtime.context import ResearchRunContext


@dataclass(frozen=True)
class LocalRunMetric:
    name: str
    status: str
    started_at: str
    ended_at: str
    detail: str = ""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_trace_links(context: ResearchRunContext, *, path: Path | None = None) -> Path:
    target = path or context.run_dir / "trace_links.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "\n".join(
            [
                "# Trace Links",
                "",
                f"- run_id: {context.run_id}",
                f"- trace_id: {context.trace_id}",
                f"- group_id: {context.trace_group_id}",
                "- dashboard: OpenAI Traces dashboard, searchable by trace id when tracing export is enabled.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return target


def write_run_metrics(context: ResearchRunContext, metrics: list[LocalRunMetric], *, path: Path | None = None) -> Path:
    target = path or context.run_dir / "run_metrics.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Run Metrics",
        "",
        f"- run_id: {context.run_id}",
        f"- trace_id: {context.trace_id}",
        f"- group_id: {context.trace_group_id}",
        "",
        "| metric | status | started_at | ended_at | detail |",
        "| --- | --- | --- | --- | --- |",
    ]
    for metric in metrics:
        detail = metric.detail.replace("|", "\\|")
        lines.append(f"| {metric.name} | {metric.status} | {metric.started_at} | {metric.ended_at} | {detail} |")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target
