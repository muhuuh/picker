from __future__ import annotations

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.outputs import SpecialistResult
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.tools.repo_tools import repo_tools


FALLBACK_PROMPT = """
You are the company research quality reviewer for the stock research repo.

Use existing run artifacts, quality reports, evidence summaries, and company-research context. Do not edit files directly.
Return a structured specialist result with quality findings, human review items, and next actions.
Focus on citation gaps, stale data, source conflicts, unsupported update proposals, overconfidence, and missing required lanes.
"""


def build_agent(context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    root = context.root if context else None
    prompt = FALLBACK_PROMPT if root is None else load_prompt(root, "agents/specialists/prompts/quality_review.md", FALLBACK_PROMPT)
    if context:
        prompt = with_memory(prompt, context.memory_context)
    return Agent[ResearchRunContext](
        name="Company Research Quality Reviewer",
        instructions=prompt,
        handoff_description="Reviews company-research outputs for source, quality, and approval-gate problems.",
        output_type=SpecialistResult,
        tools=repo_tools(),
    )
