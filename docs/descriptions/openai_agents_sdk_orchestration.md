# OpenAI Agents SDK Orchestration Design

Last updated: 2026-05-11

## Purpose

This document defines how this repo should use OpenAI Agents SDK for LLM orchestration.

The first SDK runtime foundation is implemented. It can build real SDK `Agent` objects, compose company-news, company-search, financial, filing, sentiment, risk/thesis, opportunity-assessment, writer, quality-review, Exa industry, Grok discovery, and candidate discovery specialists as tools for orchestrators, run no-model-call registry smoke checks, manually execute orchestrators over existing run artifacts, run portfolio-review and memory/evaluation packet synthesis, and run scheduled per-ticker company research plus main orchestration from the weekly wrapper behind an explicit `--execute-orchestrator` flag.

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
     -> code-level per-ticker company-research specialist fanout
     -> portfolio review over buckets, review queue, and verification results
     -> memory/evaluation review over telemetry, reflection, drafts, and finalization
     -> main orchestrator synthesis
     -> alerts, update proposals, review items, next-run plan
  -> deterministic final_digest.md/json as the human-readable fallback/summary surface
  -> human-review digest refresh and final review summary
  -> deterministic proposal review bridge
  -> quality review
  -> final run artifacts
  -> memory reflection
```

Human review policy: `agents/human_review_digest.md` is the primary user-facing inbox. `portfolio_review_orchestrator` and `memory_evaluation_orchestrator` write deeper context reports for Codex, the main orchestrator, and human drill-down. Runs should continue all independent safe work and leave only approval-gated branches waiting for the user. Notification/email automation is a later layer over the digest; email should not become a decision source until a strict, tested ingestion workflow exists.

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

Use existing repo memory through importable memory functions. The CLI form remains useful for manual inspection:

```powershell
python -m stock_research memory prompt-context --task TASK
```

This prompt-ready memory must be injected into relevant specialist prompts. Runtime context now separates:

- `memory_item_ids`: task-relevant ids that should be preferred in prompts and outputs,
- `known_memory_item_ids`: all active/needs-review ids accepted by validators.

The agent artifact should record which memory item ids materially shaped the decision.

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

Current repo/memory inspection tools are direct wrappers around Python functions, not CLI subprocesses:

- `load_repo_map`
- `load_run_summary`
- `load_quality_report`
- `load_memory_prompt_context`
- `list_evidence_packets`
- `load_evidence_packet`
- `load_run_markdown`
- `list_run_markdown_artifacts`
- `load_operational_memory`
- `load_stock_tracking_csv`

Current guarded provider/analysis execution tools are also direct wrappers around Python functions, not CLI subprocesses:

- `run_provider_tasks_guarded`
- `run_analysis_tasks_guarded`

These tools load the current run manifest from `ResearchRunContext.manifest_path` or `agents/runs/{run_id}/manifest.json`. They plan tasks by default. Live provider execution requires `execute=True`, `context.dry_run == False`, and `context.execute_providers == True`. Live analysis execution requires `execute=True`, `context.dry_run == False`, and `context.execute_analysis == True`. Otherwise, the tool returns a structured `blocked` result instead of running side effects.

## Core Function Vs CLI Vs SDK Tool

The repo should not treat CLI commands as the main architecture. The hierarchy is:

```text
importable Python function
  -> deterministic workflow calls the function directly
  -> OpenAI Agents SDK function tool wraps the function directly
  -> optional CLI command calls the function for humans, schedulers, tests, or debugging
```

Rules:

- Implement reusable behavior as an importable Python function first.
- Deterministic workflows should import and call Python functions directly, not shell out to `python -m stock_research`.
- SDK tools should wrap Python functions directly, not call CLI subprocesses.
- Add CLI commands only for high-value operational boundaries:
  - manual Codex/user-triggered runs,
  - scheduler entrypoints,
  - approval-gated side effects,
  - validation/debug commands,
  - provider smoke tests where a direct command is useful.
- Do not add a CLI command for every helper function.
- If a new CLI command is added, document whether it is user-facing, scheduler-facing, or internal/debug.

Current examples:

| Capability | Core function | CLI purpose | Future SDK tool behavior |
| --- | --- | --- | --- |
| Weekly workflow | `run_weekly_research_workflow(...)` | scheduler/manual entrypoint | usually not an agent tool |
| Proposal review bridge | `build_proposal_review(...)` | approval workflow/debug handle | guarded tool can call function directly |
| Approved proposal writer | `apply_approved_proposal(...)` | approval-gated manual/scheduler handle | writer tool should call function directly |
| Memory prompt context | `format_memory_context_for_prompt(...)` / memory loader functions | inspection/debug | specialist prompt injection should call memory code directly |

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

Current local metrics use SDK run hooks plus a local telemetry object. `run_metrics.md` records:

- `agent_run:*` rows for the overall SDK run,
- runner-level `timeout` and `error` status when live SDK execution does not complete normally,
- `agent:*` lifecycle rows,
- `llm:*` rows with token/request usage when available,
- `tool:*` rows with tool-call completion metadata,
- `memory_context:*` rows for task-relevant operational memory ids injected into the agent context,
- `memory_output:*` rows for operational memory ids reported in the final structured output.

Do not log raw tool inputs, raw tool outputs, prompts, or secrets in local metrics.

Post-run memory reflection reads `run_metrics.md`. SDK timeouts, SDK runtime errors, missing metrics for saved SDK output, and missing reported memory ids become deterministic reflection issues and memory update proposal candidates.

Human review observability should be added before scheduled automation is considered complete: run-end artifacts should record whether new HRQ rows were created, whether the digest was refreshed, and which gated branches are waiting for human input.

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

- `stock_research/agent_runtime/context.py`: `ResearchRunContext`, task-relevant memory ids, known memory ids, and task-specific memory context builder.
- `stock_research/agent_runtime/outputs.py`: typed output contracts for specialist results, orchestrator decisions, alerts, file update proposals, and human review items.
- `stock_research/agent_runtime/registry.py`: central agent registry.
- `stock_research/agent_runtime/orchestrators/main.py`: main orchestrator agent builder.
- `stock_research/agent_runtime/orchestrators/company_research.py`: first company-research sub-orchestrator, one-ticker lane packet builder for financials/company-news/filings/sentiment/company-search/risk-thesis/writer/quality lanes, fanout task builder, aggregation helper, and per-ticker scheduled artifact writer.
- `stock_research/opportunity_assessment.py`: deterministic opportunity assessment over financials, news, SEC filings, Exa context, Grok/X sentiment, and risk signals.
- `stock_research/weekly_digest.py`: deterministic final digest writer for concise run-level review summaries.
- `stock_research/agent_runtime/orchestrators/market_research.py`: first market-research sub-orchestrator for industry/theme packets, Exa web/company discovery, Grok/X trend discovery, candidate synthesis, and quality review.
- `stock_research/agent_runtime/orchestrators/portfolio_review.py`: first portfolio-review sub-orchestrator for current holdings, monitoring, rejected cooldowns, open/approved human-review items, candidate verification result reports, deterministic packet building, aggregation, and markdown report writing.
- `stock_research/agent_runtime/orchestrators/memory_evaluation.py`: first memory/evaluation sub-orchestrator for run metrics, quality reports, memory reflection, recurring failures, memory update drafts, memory writer review, finalization, deterministic packet building, aggregation, and markdown report writing.
- `stock_research/agent_runtime/reports.py`: main orchestrator aggregation packet builder covering company, market, portfolio, memory/evaluation, candidate verification, human-review digest, and review-count artifacts before final synthesis.
- `stock_research/market_research_runner.py`: manual market-research runner for user-triggered industry/theme discovery. It builds a manual manifest, can execute provider tasks, can run the SDK market fanout, extracts candidate leads into a typed schema, applies discovery quality gates, and writes a reviewable market report.
- `stock_research/candidate_review.py`: deterministic bridge from manual market-research candidate leads to reviewable candidate groups and duplicate-safe human-review queue rows. It groups duplicate listings/share classes and does not add stocks to monitoring.
- `stock_research/candidate_verification_result.py`: deterministic candidate verification result reporter that consolidates approved follow-up provider coverage, specialist statuses, findings, and next actions before promotion decisions.
- `stock_research/agent_runtime/specialists/company_news.py`: company-news specialist agent builder.
- `stock_research/agent_runtime/specialists/company_search.py`: Exa company-search specialist agent builder over existing Exa company/general search artifacts.
- `stock_research/agent_runtime/specialists/financial.py`: financial specialist agent builder over deterministic financial comparison/review artifacts.
- `stock_research/agent_runtime/specialists/filing.py`: SEC filing specialist agent builder over existing SEC EDGAR artifacts.
- `stock_research/agent_runtime/specialists/sentiment.py`: xAI/Grok sentiment specialist agent builder over existing `x_search` artifacts.
- `stock_research/agent_runtime/specialists/exa_industry.py`: Exa industry/theme/company-discovery specialist builder over existing Exa artifacts.
- `stock_research/agent_runtime/specialists/grok_discovery.py`: xAI/Grok X discovery specialist builder for niche trends, hype, rumors, and emerging ticker leads.
- `stock_research/agent_runtime/specialists/discovery.py`: candidate discovery specialist builder that combines Exa-verified and Grok-surfaced leads.
- `stock_research/agent_runtime/specialists/risk_thesis.py`: risk/thesis specialist agent builder over aggregated company-research evidence.
- `stock_research/agent_runtime/specialists/opportunity.py`: opportunity-assessment specialist agent builder for concise expert-opinion synthesis.
- `stock_research/agent_runtime/specialists/writer.py`: proposal-drafting specialist agent builder; actual file writes remain approval-gated.
- `stock_research/agent_runtime/specialists/quality_review.py`: quality-review specialist agent builder for citation/source/approval-gate checks.
- `stock_research/agent_runtime/tools/repo_tools.py`: function-first repo map, memory, run markdown, run summary, quality report, evidence packet index/loaders, and stock CSV tools. `load_evidence_packet` lets specialists inspect summarized provider-neutral JSON evidence packets directly; market discovery should not depend on markdown-only evidence exports.
- `stock_research/agent_runtime/tools/provider_tools.py`: dry-run-by-default SDK wrapper around manifest provider tasks.
- `stock_research/agent_runtime/tools/analysis_tools.py`: dry-run-by-default SDK wrapper around manifest analysis tasks.
- `stock_research/agent_runtime/runner.py`: run config wrapper with trace metadata and sensitive-data tracing disabled.
- `stock_research/agent_runtime/runner.py`: timeout/error policy that returns blocked reviewable output and writes metrics instead of silently failing.
- `stock_research/agent_runtime/fanout.py`: function-first parallel fanout helper for independent SDK agent tasks with task-specific memory, per-task timeouts, partial-failure preservation, and aggregate metrics.
- `stock_research/agent_runtime/tracing.py`: local trace/metrics artifact helpers and SDK run hooks for agent/tool/LLM/memory-id telemetry.
- `stock_research/agent_runtime/reports.py`: orchestrator input builder, runtime report writer, and output quality checks.
- `stock_research/agent_runtime/proposal_review.py`: deterministic bridge from saved SDK proposals to `orchestrator_update_proposals.md` and human-review queue rows.
- `agents/orchestrator/prompts/` and `agents/specialists/prompts/`: prompt files.
- `agents/orchestrator/specs/` and `agents/specialists/specs/`: spec files.
- CLI inspection:
  - `python -m stock_research agent-runtime list-agents`
  - `python -m stock_research agent-runtime smoke --run-id RUN_ID`
  - `python -m stock_research agent-runtime run --run-id RUN_ID`
  - `python -m stock_research agent-runtime run --run-id RUN_ID --agent-id company_research_orchestrator --ticker AAPL`
  - `python -m stock_research agent-runtime run --run-id RUN_ID --execute --write --timeout-seconds 300`
  - `python -m stock_research agent-runtime validate-output --run-id RUN_ID`
  - `python -m stock_research agent-runtime queue-proposals --run-id RUN_ID --write --queue-review`
  - `python -m stock_research agent-runtime apply-proposal --run-id RUN_ID --proposal-id ORP-0001 --write`
- Scheduled opt-in:
  - `python -m stock_research run-weekly --write --execute-orchestrator`
  - `python -m stock_research run-weekly --write --execute-providers --execute-analysis --execute-orchestrator --orchestrator-timeout-seconds 300`

Not implemented yet:

- full tool guardrail set,
- per-specialist retry policy for future fanout and deeper memory-use evaluation beyond injected/reported ids.

## Runtime Quality Gates

`quality_findings: []` means the runtime output passed deterministic gates. It is a structural and evidence-traceability signal, not an investment recommendation.

Current gates check:

- useful summary length,
- valid structured status,
- no direct buy/sell wording in the summary,
- top-level and specialist-level operational memory item ids are valid when reported,
- file update proposal targets exist,
- file update proposal `source_ids` are backed by returned sources,
- returned source references have a URL or artifact path,
- returned source artifact paths exist when provided.
- file update proposal `source_ids` may reference either returned source ids or existing repo artifact paths,
- direct trade-language checks target actual stock action patterns and should not flag ordinary business phrases.
- market candidate leads include source ids and verification status,
- Grok-only candidate leads cannot be marked for monitoring,
- active rejected-stock cooldown blocks candidate promotion,
- rumor-flagged leads remain verification-limited,
- discovery-to-monitoring promotion requires an approved `monitoring_candidate` review row plus required verification reports.
- candidate verification results surface missing provider evidence and specialist `needs_human_review` statuses before promotion.
- portfolio review reports open approvals, approved follow-ups, rejected cooldown state, and candidate verification results without applying writes.
- memory/evaluation review reports missing telemetry/reflection/finalization artifacts and ready memory drafts without applying memory updates.
- main orchestrator input aggregation lists the sub-orchestrator and review artifacts the model should inspect before final synthesis.
- human-review output should make the next user decision explicit and should route the human to the digest first, not to every deeper report.

These gates are intentionally stricter than "did the model return JSON". Future gates should add confidence calibration, contradiction handling, stale-source checks, and human-review routing checks.

Scheduled SDK runs add one more freshness gate: if provider tasks or analysis tasks were dry-run and the SDK still returns ready/actionable alerts or file update proposals, the scheduled run becomes `needs_review`. This keeps stale-artifact synthesis from being treated as fresh current-cycle research.

Fresh scheduled runs also clean generated artifacts in the target run directory before live provider/analysis execution. This prevents repeated smoke tests from leaving older evidence packets that inflate run summaries or duplicate specialist reviews.

Scheduled SDK runs also execute company-research fanout for every ticker in current holdings and monitoring before the main orchestrator. The fanout is generic: task ids include the ticker as a run label, but all specialists are reusable modules. Per-ticker reports are written under `agents/runs/{run_id}/company_research/`.

Weekly-style runs also write `agents/runs/{run_id}/final_digest.md`. This is the primary concise run-level report for humans when the live SDK main orchestrator is unavailable, too noisy, or still pending validation. It includes per-ticker opportunity view, key financial facts, Exa news/development signal, Grok/X social signal, filing coverage, watch items, and next actions.

Financial review conflict handling distinguishes material numeric conflicts from taxonomy/watch conflicts. For example, provider disagreement between `Internet Retail` and `Specialty Retail` should stay visible as a classification watch item but should not by itself mark a company as a high-risk financial conflict.

Saved SDK proposals are converted through a deterministic proposal bridge before any writer can act on them. The bridge validates the saved SDK output, writes `agents/runs/{run_id}/orchestrator_update_proposals.md`, and can append duplicate-safe rows to `agents/human_review_queue.md`. It never edits `stock_tracking/stock_info_files/`.

Approved proposals are applied through a separate deterministic writer. `agent-runtime apply-proposal` reads the proposal report, verifies the matching human-review queue row is `approved`, validates the target path is an existing markdown file under `stock_tracking/stock_info_files/`, and then updates only that company file when `--write` is passed. The writer updates `Last updated`, writes an appropriate section entry, appends `Source Log` and `Change Log` rows, and writes `agents/runs/{run_id}/applied_update_proposals.md`. It is idempotent by proposal id.

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

## Proposal Writer Result

2026-05-07 writer command shape:

```powershell
python -m stock_research agent-runtime apply-proposal --run-id 2026-05-09_weekly --proposal-id ORP-0001 --write
```

Result:

- dry-run by default without `--write`
- status: `blocked` until the matching `agents/human_review_queue.md` row is `approved`
- write scope: exactly the proposal target company file
- audit artifact: `agents/runs/{run_id}/applied_update_proposals.md`

## Candidate Verification Result

2026-05-11 validation command:

```powershell
python -m stock_research market-research candidate-verification-result --run-id 2026-05-10_manual-market-energy-storage --review-id HRQ-0007 --write --today 2026-05-11
```

Result:

- status: `needs_human_review`
- reason: FMP evidence was missing because the provider returned a subscription-limit response, and the financial review needed human review
- expected behavior: verification produced a consolidated report and did not promote the candidate
- artifact: `agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_verification_result.md`

## Portfolio Review Result

2026-05-11 validation command:

```powershell
python -m stock_research agent-runtime run --run-id 2026-05-10_manual-market-energy-storage --agent-id portfolio_review_orchestrator --task "portfolio review sub-orchestrator"
```

Result:

- status: dry-run packet build succeeded
- packet coverage: monitoring row AAPL, 8 open review items, 1 approved verification item, candidate verification result report, and no rejected cooldown rows
- deterministic report artifact: `agents/runs/2026-05-10_manual-market-energy-storage/portfolio_review/portfolio_review.md`

## Memory Evaluation Result

2026-05-11 validation command:

```powershell
python -m stock_research agent-runtime run --run-id 2026-05-10_manual-market-energy-storage --agent-id memory_evaluation_orchestrator --task "memory evaluation sub-orchestrator"
```

Result:

- status: dry-run packet build succeeded
- packet finding: the manual energy-storage run is missing run summary, quality report, memory reflection, finalization, and SDK telemetry; this correctly produces a `needs_human_review` learning-loop status when the report is written
- deterministic report artifact: `agents/runs/2026-05-10_manual-market-energy-storage/memory_evaluation/memory_evaluation.md`

## Main Aggregation Result

2026-05-11 validation command:

```powershell
python -m stock_research agent-runtime run --run-id 2026-05-10_manual-market-energy-storage --task "main orchestrator"
```

Result:

- status: dry-run packet build succeeded
- aggregation packet includes market research reports, candidate verification result, portfolio review report, memory/evaluation report, human-review digest, and open/approved review counts
- expected behavior: final synthesis has a high-level artifact map before calling specialist tools or opening deeper files

## AMZN Weekly-Style Validation

2026-05-11 validation command:

```powershell
python -m stock_research run-weekly --write --today 2026-05-11 --execute-providers --execute-analysis --execute-orchestrator --orchestrator-timeout-seconds 900
```

Result:

- provider and deterministic analysis lanes executed for current holding `AMZN` and monitoring ticker `AAPL`
- deterministic opportunity assessment report written to `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AMZN_opportunity_assessment.md`
- final digest written to `agents/runs/2026-05-16_weekly/final_digest.md`
- quality iteration corrected AMZN financial review from over-strict `needs_human_review` to `partial_review` because the only provider conflict was taxonomy/industry classification
- OpenAI Agents SDK main orchestration completed after API credit was added
- runtime quality gates were tightened to accept existing artifact-path evidence references and avoid false positives on ordinary business text such as `Sell on Amazon`
- orchestration report status is `complete` with no deterministic or SDK quality findings
- artifact: `agents/runs/2026-05-16_weekly/orchestration_report.md`
