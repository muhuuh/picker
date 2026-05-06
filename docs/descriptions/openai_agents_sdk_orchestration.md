# OpenAI Agents SDK Orchestration Design

Last updated: 2026-05-06

## Purpose

This document defines how this repo should use OpenAI Agents SDK for LLM orchestration.

The SDK runtime is not implemented yet. This file is the implementation contract for the next build slice.

Dedicated backlog: `docs/plans/openai_agents_sdk_orchestration_backlog.md`.

Dedicated scratchpad: `docs/scratchpads/openai_agents_sdk_orchestration_scratchpad.md`.

## Source Basis

Official OpenAI Agents SDK docs reviewed:

- SDK overview: https://openai.github.io/openai-agents-python/
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

## Core Design

Use OpenAI Agents SDK as the LLM orchestration layer around the existing deterministic workflow.

Keep these deterministic:

- repo state loading,
- manifest generation,
- provider task planning/execution,
- deterministic analysis task execution,
- run summary,
- quality report,
- memory reflection/finalization,
- schema validation,
- approval gates.

Use SDK agents for:

- synthesis over gathered evidence,
- deciding which bounded specialist tools to call,
- contradiction/risk analysis,
- alert and update proposal drafting,
- market/company/portfolio prioritization,
- memory/evaluation reasoning over traces and quality reports.

## Orchestration Pattern

Use a hybrid model:

1. Code orchestration controls known workflow order, dependencies, parallel fanout, retries, timeouts, and artifact persistence.
2. The main orchestrator agent handles synthesis and routing after deterministic inputs exist.
3. Specialist agents are exposed as tools when the orchestrator needs bounded subtask help.
4. Handoffs are reserved for interactive flows where the specialist should own the next user-facing turn.

This matches the repo requirement: predictable weekly coverage plus flexible agent judgment after evidence exists.

## Runtime Flow

```text
run-weekly
  -> manifest
  -> provider tasks
  -> analysis tasks
  -> run_summary
  -> quality_report
  -> memory finalize-run
  -> load prompt-ready memory context
  -> OpenAI Agents SDK runtime
     -> code-level parallel specialist calls
     -> main orchestrator synthesis
     -> alerts, update proposals, review items, next-run plan
  -> quality review
  -> final run artifacts
  -> memory reflection
```

## Planned Code Layout

```text
stock_research/agent_runtime/
  context.py
  outputs.py
  registry.py
  runner.py
  tracing.py
  guardrails.py
  tools/
  orchestrators/
  specialists/
```

Prompt/spec artifacts should live under:

```text
agents/orchestrator/
agents/specialists/
```

## Agent Composability

Every specialist should have:

- a stable input schema,
- a stable output schema,
- a direct code runner,
- an `Agent.as_tool()` wrapper for manager/orchestrator use,
- clear source/evidence requirements,
- permission boundaries for file or queue writes,
- task-relevant memory injection.

This allows the same specialist to be used in:

- scheduled weekly runs,
- manual user-triggered runs,
- sub-orchestrator fanout,
- main orchestrator tool calls,
- future evaluation tests.

## Parallel Execution

Use code-level `asyncio.gather` for independent work:

- per-ticker company research,
- per-industry/theme research,
- independent specialist reviews over already-written evidence packets,
- parallel alert/risk/contradiction checks after evidence aggregation.

Run sequentially when dependencies exist:

- provider evidence before specialist synthesis,
- Exa contents follow-up before company-news `ready_for_company_update`,
- `financial_compare` before financial synthesis,
- orchestrator synthesis before file update proposals,
- quality review before memory reflection.

## Context and Memory

Create a typed runtime context, tentatively `ResearchRunContext`, containing:

- repo root,
- run id,
- manifest path,
- run mode,
- allowed write targets,
- memory context text,
- evidence packet index,
- trace id,
- group id,
- dry-run/execute flags.

Use SDK context for dependencies and runtime state only. Do not put secrets into SDK context, traces, sessions, or artifacts.

Use existing repo memory:

```powershell
python -m stock_research memory prompt-context --task TASK
```

This prompt-ready memory must be injected into relevant specialist prompts. The agent artifact should record which memory item ids were used.

SDK sessions may be useful later for interactive Codex/manual workflows, but they are not durable project memory. Durable truth remains in repo files.

## Tools

Wrap existing deterministic code as SDK function tools:

- repo state tools,
- memory context tools,
- evidence packet tools,
- provider task tools,
- analysis task tools,
- human review queue tools,
- file update proposal tools.

Provider and analysis tools should remain dry-run by default unless the runtime context explicitly permits live execution.

File tools should be proposal-first unless a narrow writer specialist has explicit permission to edit one target file.

## Guardrails

Use tool guardrails for custom function tools because repo/provider/file tools can have side effects.

Guardrails should check:

- no secrets in tool input/output,
- source metadata is preserved,
- write target is allowed,
- generated claim has evidence or is marked unknown,
- social sentiment is labeled as sentiment, not fact,
- rejected-stock cooldown is respected,
- buy/sell/position-size suggestions become human review items.

Agent-level input/output guardrails remain useful, but they do not replace tool-level checks for side effects.

## Tracing and Metrics

Use SDK tracing for debugging and monitoring:

- workflow name,
- trace id,
- group id,
- trace metadata,
- sensitive-data setting.

Also write local audit artifacts:

- `agents/runs/{run_id}/trace_links.md`,
- `agents/runs/{run_id}/run_metrics.md`,
- optional ignored JSON metrics.

Track:

- start/end time per agent,
- duration per provider/specialist,
- tool calls,
- failures and timeouts,
- usage/token counts,
- final status,
- missing output artifacts,
- memory item ids used.

OpenAI trace data is helpful, but local artifacts are required because this repo is the durable audit trail.

## First Implementation Slice

The first SDK slice should be small and verifiable:

1. Add `openai-agents` dependency.
2. Add `stock_research/agent_runtime/` skeleton.
3. Define runtime context and structured output schemas.
4. Build one manager agent and one specialist-as-tool over existing evidence artifacts.
5. Add local tracing/metrics output.
6. Add tests and one smoke command.

Success criteria:

- no broad file writes,
- structured output validates,
- memory context is injected,
- local metrics are written,
- trace metadata is available,
- failures produce reviewable artifacts instead of silent errors.
