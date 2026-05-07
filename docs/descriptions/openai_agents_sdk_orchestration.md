# OpenAI Agents SDK Orchestration Design

Last updated: 2026-05-06

## Purpose

This document defines how this repo should use OpenAI Agents SDK for LLM orchestration.

The first SDK runtime foundation is implemented. It can build real SDK `Agent` objects, compose the company-news specialist as a tool for the main orchestrator, run no-model-call registry smoke checks, manually execute the main orchestrator over existing run artifacts, and run from the weekly wrapper behind an explicit `--execute-orchestrator` flag.

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
  -> deterministic proposal review bridge
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

## Current Implementation

Implemented:

- `stock_research/agent_runtime/context.py`: `ResearchRunContext` and memory-aware context builder.
- `stock_research/agent_runtime/outputs.py`: typed output contracts for specialist results, orchestrator decisions, alerts, file update proposals, and human review items.
- `stock_research/agent_runtime/registry.py`: central agent registry.
- `stock_research/agent_runtime/orchestrators/main.py`: main orchestrator agent builder.
- `stock_research/agent_runtime/specialists/company_news.py`: company-news specialist agent builder.
- `stock_research/agent_runtime/tools/repo_tools.py`: first repo/memory/run-artifact function tools.
- `stock_research/agent_runtime/runner.py`: run config wrapper with trace metadata and sensitive-data tracing disabled.
- `stock_research/agent_runtime/tracing.py`: local trace/metrics artifact helpers.
- `stock_research/agent_runtime/reports.py`: orchestrator input builder, runtime report writer, and output quality checks.
- `stock_research/agent_runtime/proposal_review.py`: deterministic bridge from saved SDK proposals to `orchestrator_update_proposals.md` and human-review queue rows.
- `agents/orchestrator/prompts/` and `agents/specialists/prompts/`: prompt files.
- `agents/orchestrator/specs/` and `agents/specialists/specs/`: spec files.
- CLI inspection:
  - `python -m stock_research agent-runtime list-agents`
  - `python -m stock_research agent-runtime smoke --run-id RUN_ID`
  - `python -m stock_research agent-runtime run --run-id RUN_ID`
  - `python -m stock_research agent-runtime run --run-id RUN_ID --execute --write`
  - `python -m stock_research agent-runtime validate-output --run-id RUN_ID`
  - `python -m stock_research agent-runtime queue-proposals --run-id RUN_ID --write --queue-review`
- Scheduled opt-in:
  - `python -m stock_research run-weekly --write --execute-orchestrator`
  - `python -m stock_research run-weekly --write --execute-providers --execute-analysis --execute-orchestrator`

Not implemented yet:

- parallel fanout,
- full tool guardrail set,
- additional specialists beyond company-news scaffold.

## Runtime Quality Gates

`quality_findings: []` means the runtime output passed deterministic gates. It is a structural and evidence-traceability signal, not an investment recommendation.

Current gates check:

- useful summary length,
- valid structured status,
- no direct buy/sell wording in the summary,
- top-level and specialist-level operational memory item ids are present and valid,
- file update proposal targets exist,
- file update proposal `source_ids` are backed by returned sources,
- returned source references have a URL or artifact path,
- returned source artifact paths exist when provided.

These gates are intentionally stricter than "did the model return JSON". Future gates should add confidence calibration, contradiction handling, stale-source checks, and human-review routing checks.

Scheduled SDK runs add one more freshness gate: if provider tasks or analysis tasks were dry-run and the SDK still returns ready/actionable alerts or file update proposals, the scheduled run becomes `needs_review`. This keeps stale-artifact synthesis from being treated as fresh current-cycle research.

Fresh scheduled runs also clean generated artifacts in the target run directory before live provider/analysis execution. This prevents repeated smoke tests from leaving older evidence packets that inflate run summaries or duplicate specialist reviews.

Saved SDK proposals are converted through a deterministic proposal bridge before any writer can act on them. The bridge validates the saved SDK output, writes `agents/runs/{run_id}/orchestrator_update_proposals.md`, and can append duplicate-safe rows to `agents/human_review_queue.md`. It never edits `stock_tracking/stock_info_files/`.

## Live Smoke Result

2026-05-06 live manual command:

```powershell
python -m stock_research agent-runtime run --run-id 2026-05-09_weekly --execute --write
```

Result:

- status: complete
- quality findings: none
- target file path correctly resolved from monitoring CSV: `stock_tracking/stock_info_files/monitoring/AAPL.md`
- operational memory ids recorded with valid item ids
- source-backed update proposals and source artifact paths validated
- artifacts:
  - `agents/runs/2026-05-09_weekly/agent_runtime_main_orchestrator.md`
  - `agents/runs/2026-05-09_weekly/run_metrics.md`
  - `agents/runs/2026-05-09_weekly/trace_links.md`

## Scheduled Opt-In Result

2026-05-06 scheduled command:

```powershell
python -m stock_research run-weekly --write --today 2026-05-05 --execute-orchestrator
```

Result:

- status: needs_review
- reason: provider and analysis tasks were dry-run, but the SDK produced actionable AAPL file update proposals from existing artifacts
- expected behavior: the scheduled freshness gate blocked this from being treated as a clean complete current-cycle run
- next clean live path: `python -m stock_research run-weekly --write --execute-providers --execute-analysis --execute-orchestrator`

2026-05-06 full fresh scheduled command:

```powershell
python -m stock_research run-weekly --write --today 2026-05-05 --execute-providers --execute-analysis --execute-orchestrator
```

Result:

- status: complete
- provider tasks executed: 10
- analysis tasks executed: 4
- evidence packets after cleanup: 14
- quality findings: none
- SDK quality findings: none
- notes: cleanup removed earlier smoke-test duplicates before the run summary was rebuilt

## Proposal Review Result

2026-05-07 proposal bridge command:

```powershell
python -m stock_research agent-runtime queue-proposals --run-id 2026-05-09_weekly --write --queue-review --today 2026-05-07
```

Result:

- status: ready_for_human_review
- proposals written: 2 AAPL company-file update proposals
- human review queue rows: HRQ-0002 and HRQ-0003
- artifact: `agents/runs/2026-05-09_weekly/orchestrator_update_proposals.md`
- guardrail: no company file edits were applied
