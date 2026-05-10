from __future__ import annotations

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.outputs import SpecialistResult
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.tools.repo_tools import repo_tools


FALLBACK_PROMPT = """
You are the stock-file update proposal specialist for the stock research repo.

Use existing run artifacts, company files, evidence summaries, and company-research context. Do not edit files directly.
Return structured file update proposals only when source-backed and scoped to the exact stock_info_file target.
All actual writes must go through the deterministic proposal review and approved proposal writer.
"""


def build_agent(context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    root = context.root if context else None
    prompt = FALLBACK_PROMPT if root is None else load_prompt(root, "agents/specialists/prompts/writer.md", FALLBACK_PROMPT)
    if context:
        prompt = with_memory(prompt, context.memory_context)
    return Agent[ResearchRunContext](
        name="Stock File Proposal Specialist",
        instructions=prompt,
        handoff_description="Drafts source-backed company-file update proposals without editing files.",
        output_type=SpecialistResult,
        tools=repo_tools(),
    )
