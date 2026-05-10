from __future__ import annotations

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.outputs import SpecialistResult
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.tools.repo_tools import repo_tools


FALLBACK_PROMPT = """
You are the candidate discovery specialist for the stock research repo.

Use existing Exa and Grok artifacts, strategy files, rejected cooldown state, and research priorities. Load relevant evidence packet JSON with load_evidence_packet.
Return a structured specialist result with candidate leads, strategy-fit notes, verification gaps, and human review items.
Do not promote rejected-cooldown names without flagging the cooldown. Do not treat Grok/X hype as verified fact.
"""


def build_agent(context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    root = context.root if context else None
    prompt = FALLBACK_PROMPT if root is None else load_prompt(root, "agents/specialists/prompts/discovery.md", FALLBACK_PROMPT)
    if context:
        prompt = with_memory(prompt, context.memory_context)
    return Agent[ResearchRunContext](
        name="Candidate Discovery Specialist",
        instructions=prompt,
        handoff_description="Combines Exa and Grok leads into strategy-aware candidate discovery output.",
        output_type=SpecialistResult,
        tools=repo_tools(),
    )
