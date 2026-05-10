from __future__ import annotations

from dataclasses import dataclass
import asyncio
from datetime import datetime, timezone
from typing import Any

from agents import RunConfig, Runner, flush_traces

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.registry import build_agent
from stock_research.agent_runtime.reports import evaluate_runtime_output_quality, output_to_dict, write_agent_runtime_report
from stock_research.agent_runtime.tracing import LocalRunHooks, LocalRunMetric, LocalRunTelemetry, write_run_metrics, write_trace_links


@dataclass(frozen=True)
class AgentRuntimeResult:
    agent_id: str
    final_output: Any
    trace_id: str
    group_id: str
    quality_findings: list[str]
    written_paths: tuple[str, ...] = ()
    metrics: tuple[LocalRunMetric, ...] = ()


def build_run_config(context: ResearchRunContext, *, model: str | None = None) -> RunConfig:
    return RunConfig(
        model=model,
        workflow_name="stock-research-agent-runtime",
        trace_id=context.trace_id,
        group_id=context.trace_group_id,
        trace_include_sensitive_data=False,
        trace_metadata={
            "run_id": context.run_id,
            "task": context.task,
            "dry_run": str(context.dry_run).lower(),
        },
    )


async def run_agent(
    agent_id: str,
    prompt: str,
    context: ResearchRunContext,
    *,
    model: str | None = None,
    telemetry: LocalRunTelemetry | None = None,
    timeout_seconds: float | None = None,
) -> AgentRuntimeResult:
    agent = build_agent(agent_id, context)
    runner_call = Runner.run(
        starting_agent=agent,
        input=prompt,
        context=context,
        hooks=LocalRunHooks(telemetry) if telemetry else None,
        run_config=build_run_config(context, model=model),
    )
    result = await asyncio.wait_for(runner_call, timeout=timeout_seconds) if timeout_seconds else await runner_call
    quality_findings = evaluate_runtime_output_quality(result.final_output, context)
    return AgentRuntimeResult(
        agent_id=agent_id,
        final_output=result.final_output,
        trace_id=context.trace_id,
        group_id=context.trace_group_id,
        quality_findings=quality_findings,
        written_paths=(),
        metrics=tuple(telemetry.metrics) if telemetry else (),
    )


def run_agent_sync(
    agent_id: str,
    prompt: str,
    context: ResearchRunContext,
    *,
    model: str | None = None,
    write: bool = False,
    timeout_seconds: float | None = None,
) -> AgentRuntimeResult:
    started_at = utc_now_iso()
    status = "complete"
    detail = ""
    telemetry = LocalRunTelemetry(context)
    result: AgentRuntimeResult | None = None
    try:
        result = asyncio.run(run_agent(agent_id, prompt, context, model=model, telemetry=telemetry, timeout_seconds=timeout_seconds))
        if result.quality_findings:
            status = "needs_review"
            detail = "; ".join(result.quality_findings)
    except TimeoutError:
        status = "timeout"
        detail = f"SDK agent run timed out after {timeout_seconds} second(s)."
        final_output = failure_output(agent_id, context, "blocked", detail)
        result = AgentRuntimeResult(
            agent_id=agent_id,
            final_output=final_output,
            trace_id=context.trace_id,
            group_id=context.trace_group_id,
            quality_findings=[detail],
        )
    except Exception as exc:  # noqa: BLE001 - runtime should persist reviewable failure artifacts.
        status = "error"
        detail = f"SDK agent run failed: {exc}"
        final_output = failure_output(agent_id, context, "blocked", detail)
        result = AgentRuntimeResult(
            agent_id=agent_id,
            final_output=final_output,
            trace_id=context.trace_id,
            group_id=context.trace_group_id,
            quality_findings=[detail],
        )
    finally:
        try:
            flush_traces()
        except Exception:
            pass

    ended_at = utc_now_iso()
    metrics = (
        LocalRunMetric(
            name=f"agent_run:{agent_id}",
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            detail=detail,
            memory_item_ids=context.memory_item_ids,
        ),
        LocalRunMetric(
            name=f"memory_output:{agent_id}",
            status="reported",
            started_at=ended_at,
            ended_at=ended_at,
            detail="Operational memory item ids reported by the final structured output.",
            memory_item_ids=reported_memory_item_ids(result.final_output),
        ),
        *telemetry.metrics,
    )
    written_paths: list[str] = []
    if write:
        json_path, md_path = write_agent_runtime_report(context, agent_id, result.final_output)
        trace_path = write_trace_links(context)
        metrics_path = write_run_metrics(context, list(metrics))
        written_paths = [str(json_path), str(md_path), str(trace_path), str(metrics_path)]
    return AgentRuntimeResult(
        agent_id=result.agent_id,
        final_output=result.final_output,
        trace_id=result.trace_id,
        group_id=result.group_id,
        quality_findings=result.quality_findings,
        written_paths=tuple(written_paths),
        metrics=metrics,
    )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def failure_output(agent_id: str, context: ResearchRunContext, status: str, detail: str) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "run_id": context.run_id,
        "status": status,
        "summary": (
            f"The SDK runtime did not complete normally for {agent_id}. {detail} "
            "Treat this run as needs_review and rerun or inspect the runtime metrics before accepting any synthesis."
        ),
        "memory_item_ids_used": list(context.memory_item_ids),
        "human_review_items": [
            {
                "title": "Review SDK runtime failure",
                "question": f"Should {agent_id} be rerun after resolving the runtime failure?",
                "reason": detail,
                "priority": "high",
                "source_ids": [],
            }
        ],
        "next_run_tasks": [
            f"Review `agents/runs/{context.run_id}/run_metrics.md` and rerun {agent_id} after fixing the runtime failure."
        ],
    }


def reported_memory_item_ids(output: Any) -> tuple[str, ...]:
    data = output_to_dict(output)
    ids: list[str] = []
    for item in data.get("memory_item_ids_used", []) or []:
        if item and item not in ids:
            ids.append(str(item))
    for specialist in data.get("specialist_results", []) or []:
        if not isinstance(specialist, dict):
            continue
        for item in specialist.get("memory_item_ids_used", []) or []:
            if item and item not in ids:
                ids.append(str(item))
    return tuple(ids)
