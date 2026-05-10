from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Awaitable, Callable

from stock_research.agent_runtime.context import ResearchRunContext, new_trace_id, with_task_memory
from stock_research.agent_runtime.reports import output_to_dict
from stock_research.agent_runtime.runner import AgentRuntimeResult, failure_output, run_agent, reported_memory_item_ids, utc_now_iso
from stock_research.agent_runtime.tracing import LocalRunMetric, LocalRunTelemetry


AgentRunner = Callable[..., Awaitable[AgentRuntimeResult]]


@dataclass(frozen=True)
class AgentFanoutTask:
    task_id: str
    agent_id: str
    task: str
    prompt: str
    model: str | None = None
    timeout_seconds: float | None = 300.0


@dataclass(frozen=True)
class AgentFanoutItemResult:
    task_id: str
    agent_id: str
    task: str
    status: str
    final_output: Any
    quality_findings: list[str] = field(default_factory=list)
    metrics: tuple[LocalRunMetric, ...] = ()


@dataclass(frozen=True)
class AgentFanoutResult:
    status: str
    results: tuple[AgentFanoutItemResult, ...]
    metrics: tuple[LocalRunMetric, ...]


async def run_agent_fanout(
    context: ResearchRunContext,
    tasks: list[AgentFanoutTask],
    *,
    runner: AgentRunner = run_agent,
) -> AgentFanoutResult:
    if not tasks:
        return AgentFanoutResult(status="complete", results=(), metrics=())
    results = await asyncio.gather(*(run_fanout_task(context, task, runner=runner) for task in tasks))
    statuses = {result.status for result in results}
    status = "complete" if statuses <= {"complete"} else "partial"
    return AgentFanoutResult(
        status=status,
        results=tuple(results),
        metrics=tuple(metric for result in results for metric in result.metrics),
    )


def run_agent_fanout_sync(
    context: ResearchRunContext,
    tasks: list[AgentFanoutTask],
    *,
    runner: AgentRunner = run_agent,
) -> AgentFanoutResult:
    return asyncio.run(run_agent_fanout(context, tasks, runner=runner))


async def run_fanout_task(
    parent_context: ResearchRunContext,
    task: AgentFanoutTask,
    *,
    runner: AgentRunner = run_agent,
) -> AgentFanoutItemResult:
    started_at = utc_now_iso()
    child_context = build_child_context(parent_context, task)
    telemetry = LocalRunTelemetry(child_context)
    status = "complete"
    detail = ""
    try:
        runner_call = runner(
            task.agent_id,
            task.prompt,
            child_context,
            model=task.model,
            telemetry=telemetry,
            timeout_seconds=task.timeout_seconds,
        )
        result = await asyncio.wait_for(runner_call, timeout=task.timeout_seconds) if task.timeout_seconds else await runner_call
        final_output = result.final_output
        quality_findings = result.quality_findings
        if quality_findings:
            status = "needs_review"
            detail = "; ".join(quality_findings)
    except TimeoutError:
        status = "timeout"
        detail = f"SDK fanout task {task.task_id} timed out after {task.timeout_seconds} second(s)."
        final_output = failure_output(task.agent_id, child_context, "blocked", detail)
        quality_findings = [detail]
    except Exception as exc:  # noqa: BLE001 - fanout must preserve partial results.
        status = "error"
        detail = f"SDK fanout task {task.task_id} failed: {exc}"
        final_output = failure_output(task.agent_id, child_context, "blocked", detail)
        quality_findings = [detail]

    ended_at = utc_now_iso()
    metrics = (
        LocalRunMetric(
            name=f"fanout_task:{task.task_id}",
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            detail=detail,
            memory_item_ids=child_context.memory_item_ids,
        ),
        LocalRunMetric(
            name=f"memory_output:{task.agent_id}:{task.task_id}",
            status="reported",
            started_at=ended_at,
            ended_at=ended_at,
            detail="Operational memory item ids reported by the fanout structured output.",
            memory_item_ids=reported_memory_item_ids(final_output),
        ),
        *telemetry.metrics,
    )
    return AgentFanoutItemResult(
        task_id=task.task_id,
        agent_id=task.agent_id,
        task=task.task,
        status=status,
        final_output=final_output,
        quality_findings=quality_findings,
        metrics=metrics,
    )


def build_child_context(parent_context: ResearchRunContext, task: AgentFanoutTask) -> ResearchRunContext:
    task_context = with_task_memory(parent_context, task.task)
    return replace(
        task_context,
        trace_id=new_trace_id(),
        group_id=parent_context.trace_group_id,
    )


def fanout_result_to_dict(result: AgentFanoutResult) -> dict[str, Any]:
    return {
        "status": result.status,
        "results": [
            {
                "task_id": item.task_id,
                "agent_id": item.agent_id,
                "task": item.task,
                "status": item.status,
                "final_output": output_to_dict(item.final_output),
                "quality_findings": item.quality_findings,
                "metrics": [asdict(metric) for metric in item.metrics],
            }
            for item in result.results
        ],
        "metrics": [asdict(metric) for metric in result.metrics],
    }
