from __future__ import annotations

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext
from stock_research.agent_runtime.outputs import SpecialistResult
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.tools.repo_tools import repo_tools


FALLBACK_PROMPT = """
You are the xAI/Grok X sentiment synthesis specialist for the stock research repo.

Use existing xAI/Grok x_search run artifacts and evidence summaries. Do not call X.com directly.
Return a structured specialist result with source references, confidence, alerts, update proposals, and next actions.
Label output as social sentiment or narrative signal, not verified fact. Material factual claims require verification elsewhere.
"""


def build_agent(context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    root = context.root if context else None
    prompt = FALLBACK_PROMPT if root is None else load_prompt(root, "agents/specialists/prompts/sentiment.md", FALLBACK_PROMPT)
    if context:
        prompt = with_memory(prompt, context.memory_context)
    return Agent[ResearchRunContext](
        name="xAI Grok Sentiment Specialist",
        instructions=prompt,
        handoff_description="Synthesizes existing xAI/Grok X sentiment evidence and run artifacts.",
        output_type=SpecialistResult,
        tools=repo_tools(),
    )
