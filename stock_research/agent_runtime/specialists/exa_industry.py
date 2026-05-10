from __future__ import annotations

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.outputs import SpecialistResult
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.tools.repo_tools import repo_tools


FALLBACK_PROMPT = """
You are the Exa industry/theme research specialist for the stock research repo.

Use existing Exa industry, general, news, company, and contents artifacts. Do not perform new web searches directly.
Return a structured specialist result with source references, candidate leads, confidence, and next actions.
Focus on primary web evidence, industry developments, public companies, suppliers, competitors, and verification tasks.
"""


def build_agent(context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    root = context.root if context else None
    prompt = FALLBACK_PROMPT if root is None else load_prompt(root, "agents/specialists/prompts/exa_industry.md", FALLBACK_PROMPT)
    if context:
        prompt = with_memory(prompt, context.memory_context)
    return Agent[ResearchRunContext](
        name="Exa Industry Research Specialist",
        instructions=prompt,
        handoff_description="Synthesizes existing Exa industry/theme/company-discovery artifacts.",
        output_type=SpecialistResult,
        tools=repo_tools(),
    )
