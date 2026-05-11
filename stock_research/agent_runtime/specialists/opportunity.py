from __future__ import annotations

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.outputs import SpecialistResult
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.tools.repo_tools import repo_tools


FALLBACK_PROMPT = """
You are the opportunity assessment specialist for the stock research repo.

Use existing run artifacts only: financial review, company news review, filing evidence, Grok/X sentiment, Exa company search, risk/thesis output, and the deterministic opportunity assessment report when present.
Return a structured specialist result with a concise expert-opinion summary, source references, confidence, watch items, and human-review gates.
This is research synthesis only. Do not make buy/sell/position-size instructions.
"""


def build_agent(context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    root = context.root if context else None
    prompt = FALLBACK_PROMPT if root is None else load_prompt(root, "agents/specialists/prompts/opportunity.md", FALLBACK_PROMPT)
    if context:
        prompt = with_memory(prompt, context.memory_context)
    return Agent[ResearchRunContext](
        name="Opportunity Assessment Specialist",
        instructions=prompt,
        handoff_description="Synthesizes all company research lanes into a reviewable expert-opinion opportunity assessment.",
        output_type=SpecialistResult,
        tools=repo_tools(),
    )
