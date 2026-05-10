from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.lifecycle import RunHooksBase

from stock_research.agent_runtime.context import ResearchRunContext


@dataclass(frozen=True)
class LocalRunMetric:
    name: str
    status: str
    started_at: str
    ended_at: str
    detail: str = ""
    memory_item_ids: tuple[str, ...] = ()


class LocalRunTelemetry:
    def __init__(self, context: ResearchRunContext):
        self.context = context
        self.metrics: list[LocalRunMetric] = []
        self._active: dict[str, list[str]] = {}

    def start(self, name: str) -> None:
        self._active.setdefault(name, []).append(utc_now_iso())

    def end(
        self,
        name: str,
        *,
        status: str = "complete",
        detail: str = "",
        memory_item_ids: tuple[str, ...] = (),
    ) -> None:
        started_at = self._active.get(name, []).pop() if self._active.get(name) else utc_now_iso()
        self.record(name=name, status=status, started_at=started_at, ended_at=utc_now_iso(), detail=detail, memory_item_ids=memory_item_ids)

    def record(
        self,
        *,
        name: str,
        status: str,
        started_at: str | None = None,
        ended_at: str | None = None,
        detail: str = "",
        memory_item_ids: tuple[str, ...] = (),
    ) -> None:
        timestamp = utc_now_iso()
        self.metrics.append(
            LocalRunMetric(
                name=name,
                status=status,
                started_at=started_at or timestamp,
                ended_at=ended_at or timestamp,
                detail=sanitize_detail(detail),
                memory_item_ids=memory_item_ids,
            )
        )


class LocalRunHooks(RunHooksBase[ResearchRunContext, Any]):
    def __init__(self, telemetry: LocalRunTelemetry):
        self.telemetry = telemetry

    async def on_agent_start(self, context, agent) -> None:
        agent_name = object_name(agent, "agent")
        self.telemetry.start(f"agent:{agent_name}")
        runtime_context = getattr(context, "context", None)
        memory_ids = tuple(getattr(runtime_context, "memory_item_ids", ()) or ())
        self.telemetry.record(
            name=f"memory_context:{agent_name}",
            status="injected",
            detail=f"{len(memory_ids)} task-relevant operational memory item id(s) injected.",
            memory_item_ids=memory_ids,
        )

    async def on_agent_end(self, context, agent, output: Any) -> None:
        self.telemetry.end(
            f"agent:{object_name(agent, 'agent')}",
            detail=f"output_type={type(output).__name__}",
        )

    async def on_llm_start(self, context, agent, system_prompt: str | None, input_items: list[Any]) -> None:
        self.telemetry.start(f"llm:{object_name(agent, 'agent')}")

    async def on_llm_end(self, context, agent, response) -> None:
        usage = getattr(response, "usage", None)
        detail = "usage_unavailable"
        if usage is not None:
            detail = (
                f"requests={getattr(usage, 'requests', 0)}, "
                f"input_tokens={getattr(usage, 'input_tokens', 0)}, "
                f"output_tokens={getattr(usage, 'output_tokens', 0)}, "
                f"total_tokens={getattr(usage, 'total_tokens', 0)}"
            )
        self.telemetry.end(f"llm:{object_name(agent, 'agent')}", detail=detail)

    async def on_tool_start(self, context, agent, tool) -> None:
        tool_name = object_name(tool, "tool")
        self.telemetry.start(f"tool:{tool_name}")

    async def on_tool_end(self, context, agent, tool, result: str) -> None:
        tool_name = object_name(tool, "tool")
        detail = f"result_chars={len(result or '')}"
        call_id = getattr(context, "tool_call_id", "")
        if call_id:
            detail = f"tool_call_id={call_id}; {detail}"
        self.telemetry.end(f"tool:{tool_name}", detail=detail)


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
        "| metric | status | started_at | ended_at | memory_item_ids | detail |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for metric in metrics:
        detail = metric.detail.replace("|", "\\|")
        memory_ids = ", ".join(metric.memory_item_ids).replace("|", "\\|")
        lines.append(f"| {metric.name} | {metric.status} | {metric.started_at} | {metric.ended_at} | {memory_ids} | {detail} |")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def object_name(value: Any, fallback: str) -> str:
    name = getattr(value, "name", "") or getattr(value, "__name__", "")
    return str(name or type(value).__name__ or fallback).replace("|", "\\|")


def sanitize_detail(value: str, limit: int = 300) -> str:
    normalized = " ".join(str(value).split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."
