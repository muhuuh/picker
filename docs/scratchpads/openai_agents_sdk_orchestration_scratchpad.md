# OpenAI Agents SDK Orchestration Scratchpad

> Living scratchpad for the OpenAI Agents SDK runtime decision and implementation.
> Keep entries short and scannable. Do not store secrets.

## Goal

- Build the LLM orchestration runtime on OpenAI Agents SDK.
- Keep deterministic kickoff, provider execution, analysis tasks, memory finalization, and quality checks as the reliable foundation.
- Add composable orchestrator and specialist agents that can be run from scheduled workflows, manual Codex-triggered workflows, or as bounded tools.

## Current Decision

- 2026-05-06: User selected OpenAI Agents SDK as the preferred agent framework.
- 2026-05-06: The framework decision boundary in `run-weekly` should now become an OpenAI Agents SDK integration boundary.
- 2026-05-06: Runtime code should be importable/testable under `stock_research/agent_runtime/`; prompts/specs can live under `agents/orchestrator/` and `agents/specialists/`.
- 2026-05-06: First runtime foundation implemented: dependency, context, outputs, registry, main orchestrator builder, company-news specialist builder, specialist-as-tool composition, prompt/spec folders, repo tools, run config wrapper, trace helpers, tests, and no-model-call smoke CLI.

## Official Docs Reviewed

- OpenAI Agents SDK overview: https://openai.github.io/openai-agents-python/
- Agents: https://openai.github.io/openai-agents-python/agents/
- Agent orchestration: https://openai.github.io/openai-agents-python/multi_agent/
- Running agents: https://openai.github.io/openai-agents-python/running_agents/
- Tools: https://openai.github.io/openai-agents-python/tools/
- Guardrails: https://openai.github.io/openai-agents-python/guardrails/
- Tracing: https://openai.github.io/openai-agents-python/tracing/
- Sessions: https://openai.github.io/openai-agents-python/sessions/
- Results: https://openai.github.io/openai-agents-python/results/
- Usage: https://openai.github.io/openai-agents-python/usage/
- Models: https://openai.github.io/openai-agents-python/models/
- Context management: https://openai.github.io/openai-agents-python/context/

## Findings

- SDK primitives match this repo: agents, function tools, agents as tools, handoffs, guardrails, sessions, tracing, structured outputs, and usage tracking.
- Use code orchestration for deterministic workflow order, dependency handling, parallel fanout, retries, and cost control.
- Use LLM orchestration for synthesis, prioritization, contradiction detection, and deciding which bounded tools/specialists to call after deterministic inputs exist.
- Use manager-style `Agent.as_tool()` for specialist calls when the main orchestrator should own the final synthesis.
- Use handoffs sparingly, mainly for interactive Codex/user triage where a specialist should own the next conversational turn.
- Use `asyncio.gather` around independent `Runner.run(...)` calls for parallel specialist work, not hidden prompt-only parallelism.
- Use structured outputs through `output_type` for orchestrator decisions, specialist reviews, update proposals, and alert packets.
- Use `RunConfig` for workflow name, trace id, group id, metadata, model defaults, and sensitive-data trace settings.
- Use SDK tracing plus local run artifacts. OpenAI traces are useful, but repo-local `trace_links.md`, run metrics, and finalization artifacts remain the audit surface.
- Use SDK usage tracking and hooks to persist request counts, token usage, model calls, and durations into run metrics.
- Use tool guardrails on custom function tools. Agent-level guardrails only cover workflow boundaries; file/provider tools need their own validation.
- Use SDK sessions for conversation/runtime continuity, not as the durable investment memory. Durable truth stays in repo files and `agents/memory/`.
- Do not put secrets into `RunContextWrapper.context`, traces, sessions, or repo artifacts.

## Proposed Runtime Shape

```text
stock_research/agent_runtime/
  __init__.py
  context.py              # run id, repo root, manifest paths, memory context, permissions
  registry.py             # agent/tool registry and construction helpers
  runner.py               # SDK Runner wrappers, async fanout, aggregation, errors
  tracing.py              # trace ids, local metrics, trace_links.md, hooks
  guardrails.py           # source metadata, secret redaction, file-write restrictions
  outputs.py              # Pydantic output contracts for orchestrators/specialists
  tools/
    repo_tools.py         # read repo map, load memory, inspect artifacts
    provider_tools.py     # wrappers around existing deterministic provider commands/functions
    analysis_tools.py     # wrappers around financial/news specialist deterministic steps
    memory_tools.py       # prompt-context, draft/apply flow, human review queue
    writer_tools.py       # proposal-only file updates, scoped by target file
  orchestrators/
    main.py
    company_research.py
    market_research.py
    portfolio_review.py
    memory_evaluation.py
  specialists/
    financial.py
    company_news.py
    grok_sentiment.py
    exa_industry.py
    filing.py
    risk.py
    writer.py

agents/
  orchestrator/
    prompts/
    specs/
  specialists/
    prompts/
    specs/
```

## Workflow Fit

```text
run-weekly
  -> deterministic manifest/provider/analysis/summary/quality/memory finalization
  -> load task-relevant operational memory
  -> OpenAI Agents SDK orchestration runtime
     -> code-orchestrated parallel specialist fanout where dependencies allow
     -> manager/orchestrator agent uses specialist agents as tools for bounded synthesis
     -> structured outputs become alerts, update proposals, review queue items, and next-run tasks
  -> quality review
  -> memory reflection and finalization
```

## Key Design Decisions

- Keep existing deterministic tools as first-class Python functions and expose them to agents as function tools.
- Treat specialist agents as composable units: callable directly by scheduled code, callable as `Agent.as_tool()` by orchestrators, and usable in deterministic task chains through stable input/output contracts.
- Give every agent run a `run_id`, `task_id`, `agent_id`, `trace_id`, `group_id`, and structured output path.
- Store local observability artifacts even when OpenAI tracing is enabled.
- Keep file writes proposal-first by default. Writer tools may only edit assigned files after validation or explicit workflow permission.

## Open Questions

- Which OpenAI model should be the default for orchestrator vs low-risk specialists? Defer model optimization until the first runtime spike works.
- Should the first SDK-backed specialist be company-news synthesis, Grok sentiment synthesis, or main orchestrator synthesis over existing deterministic artifacts?
- Should sessions use SQLite initially, or should early scheduled runs avoid sessions and use explicit repo artifacts only?
- What exact local trace metrics format should be persisted: JSON-only, markdown summary, or both?

## Next Steps

- Add OpenAI Agents SDK dependency only when implementing the first runtime spike.
- Build a minimal SDK runtime spike with one manager agent, one specialist-as-tool, structured output, tool guardrails, local metrics, and trace metadata.
- Wire `run-weekly` to optionally call the SDK runtime after deterministic finalization.
- Add tests with fake tools/model paths where possible before live API smoke tests.

## Risks / Gotchas

- Traces may include sensitive LLM/tool inputs by default; configure sensitive-data handling deliberately.
- Agent-as-tool currently does not expose tool-guardrail options directly, so guard critical logic inside wrapped function tools or the specialist runner.
- Handoffs transfer conversation control and can make audit boundaries less clear; use them only when that behavior is intentional.
- SDK sessions are convenient but not a substitute for repo memory, evidence packets, or run artifacts.
- Parallel fanout needs explicit timeout/error handling so one slow provider/specialist does not block the whole weekly run.

## Commands / Env Notes

- Future dependency: `openai-agents`.
- Future live runtime env: `OPENAI_API_KEY`.
- Existing prompt memory command for runtime injection: `python -m stock_research memory prompt-context --task TASK`.
- Existing deterministic weekly boundary: `python -m stock_research run-weekly --write`.
- SDK registry smoke command: `python -m stock_research agent-runtime smoke --run-id 2026-05-09_weekly`.
- Dependency install command used: `python -m pip install -e .`.
- Install warning observed: `openai-agents` pulled `starlette 1.0.0`, which conflicts with an unrelated installed `fastapi 0.117.1` requirement in this environment. The repo does not currently use FastAPI, but revisit this if a FastAPI service is added later.
