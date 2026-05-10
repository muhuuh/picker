from __future__ import annotations

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.outputs import SpecialistResult
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.tools.repo_tools import repo_tools


FALLBACK_PROMPT = """
You are the xAI/Grok X discovery specialist for the stock research repo.

Use existing xAI/Grok x_search artifacts. Do not use direct X.com APIs.
Return a structured specialist result with social-signal leads, hype/rumor assessment, citations, confidence, and verification next actions.
Treat X output as sentiment, narrative, and lead generation only; material claims must be verified with Exa, filings, or market-data providers.
"""


def build_agent(context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    root = context.root if context else None
    prompt = FALLBACK_PROMPT if root is None else load_prompt(root, "agents/specialists/prompts/grok_discovery.md", FALLBACK_PROMPT)
    if context:
        prompt = with_memory(prompt, context.memory_context)
    return Agent[ResearchRunContext](
        name="xAI Grok X Discovery Specialist",
        instructions=prompt,
        handoff_description="Synthesizes X-based trend, hype, rumor, and niche company-discovery signals.",
        output_type=SpecialistResult,
        tools=repo_tools(),
    )
