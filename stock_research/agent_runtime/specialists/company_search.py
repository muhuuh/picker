from __future__ import annotations

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.outputs import SpecialistResult
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.tools.repo_tools import repo_tools


FALLBACK_PROMPT = """
You are the Exa company-search synthesis specialist for the stock research repo.

Use existing Exa company/general search artifacts and evidence summaries. Do not perform new web searches directly.
Return a structured specialist result with source references, confidence, alerts, update proposals, and next actions.
Focus on company identity, business context, source discovery, competitor/supplier context, and claims that need contents follow-up.
"""


def build_agent(context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    root = context.root if context else None
    prompt = FALLBACK_PROMPT if root is None else load_prompt(root, "agents/specialists/prompts/company_search.md", FALLBACK_PROMPT)
    if context:
        prompt = with_memory(prompt, context.memory_context)
    return Agent[ResearchRunContext](
        name="Exa Company Search Specialist",
        instructions=prompt,
        handoff_description="Synthesizes existing Exa company/general search evidence and run artifacts.",
        output_type=SpecialistResult,
        tools=repo_tools(),
    )
