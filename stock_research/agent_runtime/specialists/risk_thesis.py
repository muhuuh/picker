from __future__ import annotations

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.outputs import SpecialistResult
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.tools.repo_tools import repo_tools


FALLBACK_PROMPT = """
You are the risk and thesis-impact specialist for the stock research repo.

Use existing run artifacts, company files, and evidence summaries. Do not fetch new data directly.
Return a structured specialist result with source references, confidence, alerts, update proposals, and next actions.
Focus on contradictions, stale thesis assumptions, new risks, thesis-impact severity, and evidence gaps.
"""


def build_agent(context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    root = context.root if context else None
    prompt = FALLBACK_PROMPT if root is None else load_prompt(root, "agents/specialists/prompts/risk_thesis.md", FALLBACK_PROMPT)
    if context:
        prompt = with_memory(prompt, context.memory_context)
    return Agent[ResearchRunContext](
        name="Risk Thesis Specialist",
        instructions=prompt,
        handoff_description="Synthesizes risks, contradictions, stale thesis assumptions, and thesis impact.",
        output_type=SpecialistResult,
        tools=repo_tools(),
    )
