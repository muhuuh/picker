from __future__ import annotations

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.outputs import SpecialistResult
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.tools.repo_tools import repo_tools


FALLBACK_PROMPT = """
You are the financial synthesis specialist for the stock research repo.

Use existing deterministic financial artifacts only. Start from financial_compare and financial_data_specialist review outputs.
Return a structured specialist result with source references, confidence, alerts, update proposals, and next actions.
Preserve provider conflicts. Do not treat Exa or Grok as financial metric sources. Do not make buy/sell recommendations.
"""


def build_agent(context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    root = context.root if context else None
    prompt = FALLBACK_PROMPT if root is None else load_prompt(root, "agents/specialists/prompts/financial.md", FALLBACK_PROMPT)
    if context:
        prompt = with_memory(prompt, context.memory_context)
    return Agent[ResearchRunContext](
        name="Financial Specialist",
        instructions=prompt,
        handoff_description="Synthesizes existing financial comparison and financial review artifacts.",
        output_type=SpecialistResult,
        tools=repo_tools(),
    )
