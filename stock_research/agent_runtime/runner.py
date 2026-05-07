from __future__ import annotations

from dataclasses import dataclass
import asyncio
from datetime import datetime, timezone
from typing import Any

from agents import RunConfig, Runner, flush_traces

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.registry import build_agent
from stock_research.agent_runtime.reports import evaluate_runtime_output_quality, write_agent_runtime_report
from stock_research.agent_runtime.tracing import LocalRunMetric, write_run_metrics, write_trace_links


@dataclass(frozen=True)
class AgentRuntimeResult:
    agent_id: str
    final_output: Any
    trace_id: str
    group_id: str
    quality_findings: list[str]
    written_paths: tuple[str, ...] = ()


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


async def run_agent(agent_id: str, prompt: str, context: ResearchRunContext, *, model: str | None = None) -> AgentRuntimeResult:
    agent = build_agent(agent_id, context)
    started_at = utc_now_iso()
    result = await Runner.run(
        starting_agent=agent,
        input=prompt,
        context=context,
        run_config=build_run_config(context, model=model),
    )
    ended_at = utc_now_iso()
    quality_findings = evaluate_runtime_output_quality(result.final_output, context)
    return AgentRuntimeResult(
        agent_id=agent_id,
        final_output=result.final_output,
        trace_id=context.trace_id,
        group_id=context.trace_group_id,
        quality_findings=quality_findings,
        written_paths=(),
    )


def run_agent_sync(
    agent_id: str,
    prompt: str,
    context: ResearchRunContext,
    *,
    model: str | None = None,
    write: bool = False,
) -> AgentRuntimeResult:
    started_at = utc_now_iso()
    status = "complete"
    detail = ""
    try:
        result = asyncio.run(run_agent(agent_id, prompt, context, model=model))
        if result.quality_findings:
            status = "needs_review"
            detail = "; ".join(result.quality_findings)
        written_paths: list[str] = []
        if write:
            json_path, md_path = write_agent_runtime_report(context, agent_id, result.final_output)
            trace_path = write_trace_links(context)
            metrics_path = write_run_metrics(
                context,
                [
                    LocalRunMetric(
                        name=f"agent:{agent_id}",
                        status=status,
                        started_at=started_at,
                        ended_at=utc_now_iso(),
                        detail=detail,
                    )
                ],
            )
            written_paths = [str(json_path), str(md_path), str(trace_path), str(metrics_path)]
        return AgentRuntimeResult(
            agent_id=result.agent_id,
            final_output=result.final_output,
            trace_id=result.trace_id,
            group_id=result.group_id,
            quality_findings=result.quality_findings,
            written_paths=tuple(written_paths),
        )
    except Exception:
        status = "error"
        raise
    finally:
        try:
            flush_traces()
        except Exception:
            pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
