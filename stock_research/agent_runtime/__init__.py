"""OpenAI Agents SDK runtime scaffolding for stock research orchestration."""

__all__ = [
    "AgentSpec",
    "ResearchRunContext",
    "build_agent",
    "build_agent_tool",
    "build_research_run_context",
    "list_agent_specs",
]


def __getattr__(name):
    if name in {"ResearchRunContext", "build_research_run_context"}:
        from .context import ResearchRunContext, build_research_run_context

        values = {
            "ResearchRunContext": ResearchRunContext,
            "build_research_run_context": build_research_run_context,
        }
        return values[name]
    if name in {"AgentSpec", "build_agent", "build_agent_tool", "list_agent_specs"}:
        from .registry import AgentSpec, build_agent, build_agent_tool, list_agent_specs

        values = {
            "AgentSpec": AgentSpec,
            "build_agent": build_agent,
            "build_agent_tool": build_agent_tool,
            "list_agent_specs": list_agent_specs,
        }
        return values[name]
    raise AttributeError(name)
