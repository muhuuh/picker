from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.orchestrators.company_research import build_agent as build_company_research_orchestrator
from stock_research.agent_runtime.orchestrators.main import build_agent as build_main_orchestrator
from stock_research.agent_runtime.orchestrators.market_research import build_agent as build_market_research_orchestrator
from stock_research.agent_runtime.orchestrators.memory_evaluation import build_agent as build_memory_evaluation_orchestrator
from stock_research.agent_runtime.orchestrators.portfolio_review import build_agent as build_portfolio_review_orchestrator
from stock_research.agent_runtime.specialists.company_news import build_agent as build_company_news_specialist
from stock_research.agent_runtime.specialists.company_search import build_agent as build_company_search_specialist
from stock_research.agent_runtime.specialists.discovery import build_agent as build_discovery_specialist
from stock_research.agent_runtime.specialists.exa_industry import build_agent as build_exa_industry_specialist
from stock_research.agent_runtime.specialists.filing import build_agent as build_filing_specialist
from stock_research.agent_runtime.specialists.financial import build_agent as build_financial_specialist
from stock_research.agent_runtime.specialists.grok_discovery import build_agent as build_grok_discovery_specialist
from stock_research.agent_runtime.specialists.quality_review import build_agent as build_quality_reviewer_specialist
from stock_research.agent_runtime.specialists.risk_thesis import build_agent as build_risk_thesis_specialist
from stock_research.agent_runtime.specialists.sentiment import build_agent as build_sentiment_specialist
from stock_research.agent_runtime.specialists.writer import build_agent as build_writer_specialist


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
    "market_research_orchestrator": AgentSpec(
        agent_id="market_research_orchestrator",
        role="orchestrator",
        description="Sub-orchestrator that coordinates industry/theme research, Grok/X trend discovery, and candidate discovery.",
        builder=build_market_research_orchestrator,
    ),
    "portfolio_review_orchestrator": AgentSpec(
        agent_id="portfolio_review_orchestrator",
        role="orchestrator",
        description="Sub-orchestrator that reviews holdings, monitoring names, rejected cooldowns, open approvals, and next actions.",
        builder=build_portfolio_review_orchestrator,
    ),
    "memory_evaluation_orchestrator": AgentSpec(
        agent_id="memory_evaluation_orchestrator",
        role="orchestrator",
        description="Sub-orchestrator that reviews run telemetry, memory reflection, memory drafts, and learning-loop health.",
        builder=build_memory_evaluation_orchestrator,
    ),
    "company_news_specialist": AgentSpec(
        agent_id="company_news_specialist",
        role="specialist",
        description="Specialist agent that synthesizes existing company-news evidence and run artifacts.",
        builder=build_company_news_specialist,
    ),
    "company_search_specialist": AgentSpec(
        agent_id="company_search_specialist",
        role="specialist",
        description="Specialist agent that synthesizes existing Exa company/general search artifacts.",
        builder=build_company_search_specialist,
    ),
    "discovery_specialist": AgentSpec(
        agent_id="discovery_specialist",
        role="specialist",
        description="Specialist agent that combines Exa-verified and Grok-surfaced leads into candidate discovery output.",
        builder=build_discovery_specialist,
    ),
    "exa_industry_specialist": AgentSpec(
        agent_id="exa_industry_specialist",
        role="specialist",
        description="Specialist agent that synthesizes existing Exa industry/theme/company-discovery artifacts.",
        builder=build_exa_industry_specialist,
    ),
    "financial_specialist": AgentSpec(
        agent_id="financial_specialist",
        role="specialist",
        description="Specialist agent that synthesizes existing financial comparison and review artifacts.",
        builder=build_financial_specialist,
    ),
    "grok_discovery_specialist": AgentSpec(
        agent_id="grok_discovery_specialist",
        role="specialist",
        description="Specialist agent that synthesizes xAI/Grok X trend, hype, rumor, and niche company-discovery signals.",
        builder=build_grok_discovery_specialist,
    ),
    "filing_specialist": AgentSpec(
        agent_id="filing_specialist",
        role="specialist",
        description="Specialist agent that synthesizes existing SEC EDGAR filing artifacts.",
        builder=build_filing_specialist,
    ),
    "quality_reviewer_specialist": AgentSpec(
        agent_id="quality_reviewer_specialist",
        role="specialist",
        description="Specialist agent that reviews company-research outputs for source, quality, and approval-gate issues.",
        builder=build_quality_reviewer_specialist,
    ),
    "risk_thesis_specialist": AgentSpec(
        agent_id="risk_thesis_specialist",
        role="specialist",
        description="Specialist agent that synthesizes risk, contradiction, and thesis-impact evidence.",
        builder=build_risk_thesis_specialist,
    ),
    "sentiment_specialist": AgentSpec(
        agent_id="sentiment_specialist",
        role="specialist",
        description="Specialist agent that synthesizes existing xAI/Grok X sentiment artifacts.",
        builder=build_sentiment_specialist,
    ),
    "writer_specialist": AgentSpec(
        agent_id="writer_specialist",
        role="specialist",
        description="Specialist agent that drafts source-backed company-file update proposals without editing files.",
        builder=build_writer_specialist,
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
