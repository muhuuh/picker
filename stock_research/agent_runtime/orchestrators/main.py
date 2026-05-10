from __future__ import annotations

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext, with_task_memory
from stock_research.agent_runtime.outputs import OrchestratorDecision
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.specialists.company_news import build_agent as build_company_news_agent
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
        ],
    )
