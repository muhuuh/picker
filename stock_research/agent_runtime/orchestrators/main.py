from __future__ import annotations

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext, with_task_memory
from stock_research.agent_runtime.outputs import OrchestratorDecision
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.orchestrators.company_research import build_agent as build_company_research_agent
from stock_research.agent_runtime.orchestrators.market_research import build_agent as build_market_research_agent
from stock_research.agent_runtime.orchestrators.portfolio_review import build_agent as build_portfolio_review_agent
from stock_research.agent_runtime.specialists.company_news import build_agent as build_company_news_agent
from stock_research.agent_runtime.specialists.company_search import build_agent as build_company_search_agent
from stock_research.agent_runtime.specialists.discovery import build_agent as build_discovery_agent
from stock_research.agent_runtime.specialists.exa_industry import build_agent as build_exa_industry_agent
from stock_research.agent_runtime.specialists.filing import build_agent as build_filing_agent
from stock_research.agent_runtime.specialists.financial import build_agent as build_financial_agent
from stock_research.agent_runtime.specialists.grok_discovery import build_agent as build_grok_discovery_agent
from stock_research.agent_runtime.specialists.quality_review import build_agent as build_quality_review_agent
from stock_research.agent_runtime.specialists.risk_thesis import build_agent as build_risk_thesis_agent
from stock_research.agent_runtime.specialists.sentiment import build_agent as build_sentiment_agent
from stock_research.agent_runtime.specialists.writer import build_agent as build_writer_agent
from stock_research.agent_runtime.tools.analysis_tools import analysis_tools
from stock_research.agent_runtime.tools.provider_tools import provider_tools
from stock_research.agent_runtime.tools.repo_tools import repo_tools


FALLBACK_PROMPT = """
You are the main stock research orchestrator.

Start from deterministic run artifacts, operational memory, and specialist outputs. Use specialist tools for bounded analysis.
Return structured decisions only: alerts, file update proposals, human review items, and next-run tasks.
Do not directly trade. Do not directly edit company files. Preserve uncertainty and source gaps.
"""


def build_agent(context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    root = context.root if context else None
    prompt = FALLBACK_PROMPT if root is None else load_prompt(root, "agents/orchestrator/prompts/main.md", FALLBACK_PROMPT)
    if context:
        prompt = with_memory(prompt, context.memory_context)

    company_news_context = with_task_memory(context, "company news specialist") if context else None
    company_news_agent = build_company_news_agent(company_news_context)
    company_search_context = with_task_memory(context, "Exa company search specialist") if context else None
    company_search_agent = build_company_search_agent(company_search_context)
    financial_context = with_task_memory(context, "financial specialist") if context else None
    financial_agent = build_financial_agent(financial_context)
    filing_context = with_task_memory(context, "SEC filing specialist") if context else None
    filing_agent = build_filing_agent(filing_context)
    sentiment_context = with_task_memory(context, "xAI Grok stock sentiment specialist") if context else None
    sentiment_agent = build_sentiment_agent(sentiment_context)
    risk_context = with_task_memory(context, "risk thesis specialist") if context else None
    risk_agent = build_risk_thesis_agent(risk_context)
    writer_context = with_task_memory(context, "writer specialist") if context else None
    writer_agent = build_writer_agent(writer_context)
    quality_context = with_task_memory(context, "quality reviewer specialist") if context else None
    quality_agent = build_quality_review_agent(quality_context)
    exa_industry_context = with_task_memory(context, "Exa industry research specialist") if context else None
    exa_industry_agent = build_exa_industry_agent(exa_industry_context)
    grok_discovery_context = with_task_memory(context, "xAI Grok industry sentiment specialist") if context else None
    grok_discovery_agent = build_grok_discovery_agent(grok_discovery_context)
    discovery_context = with_task_memory(context, "discovery specialist") if context else None
    discovery_agent = build_discovery_agent(discovery_context)
    company_research_context = with_task_memory(context, "company research sub-orchestrator") if context else None
    company_research_agent = build_company_research_agent(company_research_context)
    market_research_context = with_task_memory(context, "market research sub-orchestrator") if context else None
    market_research_agent = build_market_research_agent(market_research_context)
    portfolio_review_context = with_task_memory(context, "portfolio review sub-orchestrator") if context else None
    portfolio_review_agent = build_portfolio_review_agent(portfolio_review_context)
    return Agent[ResearchRunContext](
        name="Main Stock Research Orchestrator",
        instructions=prompt,
        output_type=OrchestratorDecision,
        tools=[
            *repo_tools(),
            *provider_tools(),
            *analysis_tools(),
            company_news_agent.as_tool(
                tool_name="company_news_specialist",
                tool_description="Review existing company-news artifacts and produce a structured specialist result.",
            ),
            company_search_agent.as_tool(
                tool_name="company_search_specialist",
                tool_description="Review existing Exa company/general search artifacts.",
            ),
            financial_agent.as_tool(
                tool_name="financial_specialist",
                tool_description="Review existing financial comparison and financial-data specialist artifacts.",
            ),
            filing_agent.as_tool(
                tool_name="filing_specialist",
                tool_description="Review existing SEC EDGAR filing artifacts.",
            ),
            sentiment_agent.as_tool(
                tool_name="sentiment_specialist",
                tool_description="Review existing xAI/Grok X sentiment artifacts and label social signals carefully.",
            ),
            risk_agent.as_tool(
                tool_name="risk_thesis_specialist",
                tool_description="Review risks, contradictions, stale thesis assumptions, and thesis impact.",
            ),
            writer_agent.as_tool(
                tool_name="writer_specialist",
                tool_description="Draft source-backed company-file update proposals without editing files.",
            ),
            quality_agent.as_tool(
                tool_name="quality_reviewer_specialist",
                tool_description="Review company-research output quality, citations, source gaps, and approval gates.",
            ),
            exa_industry_agent.as_tool(
                tool_name="exa_industry_specialist",
                tool_description="Review existing Exa industry/theme/company-discovery artifacts.",
            ),
            grok_discovery_agent.as_tool(
                tool_name="grok_discovery_specialist",
                tool_description="Review existing xAI/Grok X trend, hype, rumor, sentiment, and emerging ticker artifacts.",
            ),
            discovery_agent.as_tool(
                tool_name="discovery_specialist",
                tool_description="Combine Exa-verified and Grok-surfaced leads into candidate discovery output.",
            ),
            company_research_agent.as_tool(
                tool_name="company_research_orchestrator",
                tool_description="Coordinate one-ticker company research across financials, news, filings, sentiment, and update proposals.",
            ),
            market_research_agent.as_tool(
                tool_name="market_research_orchestrator",
                tool_description="Coordinate industry/theme research, Grok/X trend discovery, and candidate discovery.",
            ),
            portfolio_review_agent.as_tool(
                tool_name="portfolio_review_orchestrator",
                tool_description="Review holdings, monitoring names, rejected cooldowns, open approvals, and next actions.",
            ),
        ],
    )
