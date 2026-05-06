from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents import RunConfig, Runner

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.registry import build_agent


@dataclass(frozen=True)
class AgentRuntimeResult:
    agent_id: str
    final_output: Any
    trace_id: str
    group_id: str


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
    result = await Runner.run(
        starting_agent=agent,
        input=prompt,
        context=context,
        run_config=build_run_config(context, model=model),
    )
    return AgentRuntimeResult(
        agent_id=agent_id,
        final_output=result.final_output,
        trace_id=context.trace_id,
        group_id=context.trace_group_id,
    )
