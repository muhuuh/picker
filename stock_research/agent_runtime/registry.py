from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.orchestrators.company_research import build_agent as build_company_research_orchestrator
from stock_research.agent_runtime.orchestrators.main import build_agent as build_main_orchestrator
from stock_research.agent_runtime.specialists.company_news import build_agent as build_company_news_specialist


AgentRole = Literal["orchestrator", "specialist"]
AgentBuilder = Callable[[ResearchRunContext | None], Agent[ResearchRunContext]]


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    role: AgentRole
    description: str
    builder: AgentBuilder


_AGENT_SPECS: dict[str, AgentSpec] = {
    "main_orchestrator": AgentSpec(
        agent_id="main_orchestrator",
        role="orchestrator",
        description="Main manager agent that synthesizes deterministic artifacts and calls bounded specialist tools.",
        builder=build_main_orchestrator,
    ),
    "company_research_orchestrator": AgentSpec(
        agent_id="company_research_orchestrator",
        role="orchestrator",
        description="Sub-orchestrator that coordinates one-ticker company research across evidence lanes and bounded specialists.",
        builder=build_company_research_orchestrator,
    ),
    "company_news_specialist": AgentSpec(
        agent_id="company_news_specialist",
        role="specialist",
        description="Specialist agent that synthesizes existing company-news evidence and run artifacts.",
        builder=build_company_news_specialist,
    ),
}


def list_agent_specs(role: AgentRole | None = None) -> list[AgentSpec]:
    specs = sorted(_AGENT_SPECS.values(), key=lambda spec: spec.agent_id)
    if role:
        specs = [spec for spec in specs if spec.role == role]
    return specs


def build_agent(agent_id: str, context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    try:
        spec = _AGENT_SPECS[agent_id]
    except KeyError as exc:
        known = ", ".join(sorted(_AGENT_SPECS))
        raise ValueError(f"Unknown agent id: {agent_id}. Known agents: {known}") from exc
    return spec.builder(context)


def build_agent_tool(agent_id: str, context: ResearchRunContext | None = None, *, tool_name: str | None = None, tool_description: str | None = None):
    spec = _AGENT_SPECS.get(agent_id)
    if not spec:
        known = ", ".join(sorted(_AGENT_SPECS))
        raise ValueError(f"Unknown agent id: {agent_id}. Known agents: {known}")
    agent = spec.builder(context)
    return agent.as_tool(
        tool_name=tool_name or spec.agent_id,
        tool_description=tool_description or spec.description,
    )
