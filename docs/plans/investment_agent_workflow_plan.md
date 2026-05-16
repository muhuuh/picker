# Investment Agent Workflow Plan

Last updated: 2026-05-11

## Goal and Scope

Design and build a Python-based automated stock tracking and investment research workflow. The system should maintain `stock_tracking/`, gather new evidence through scheduled deterministic steps, use specialist agents for narrow research tasks, and let a main orchestrator synthesize next actions.

This plan covers architecture, repo conventions, agent roles, memory, and implementation sequencing.

Detailed backlog: `docs/plans/investment_agent_backlog.md`.

## Priority 0: Validate Architecture

- [x] Draft initial workflow architecture.
- [x] Define proposed stock tracking file model.
- [x] Define proposed orchestrator, sub-orchestrator, and specialist roles.
- [x] Define proposed memory and run-artifact model.
- [x] Record user decisions on scope, alert goals, providers, cadence, and rejected-stock cooldown.
- [x] Add human-to-system intake model with separate input and review queues.
- [x] Add digest-first human review operating model for asynchronous approval.
- [ ] User validates final architecture after these decisions.
- [x] Decide first implementation slice.

## Priority 1: Establish Repo State Files

- [x] Create category CSV schemas for current holdings, monitoring, and rejected stocks.
- [x] Create category state markdown templates.
- [x] Create company stock-info markdown template.
- [x] Create strategy files: investment strategy, screening criteria, risk rules.
- [x] Create market research folder conventions.
- [x] Add rejected-stock cooldown fields: date rejected, reject reason, next eligible review date.
- [ ] Add README/SETUP once runtime setup begins.

## Priority 2: Build Deterministic Core

- [x] Implement human input queue loader.
- [x] Implement research priorities loader.
- [x] Include human-request items in weekly run manifest generation.
- [x] Include human review queue in repo state loading.

- [x] Implement repo state loader.
- [x] Implement CSV schema validator.
- [x] Implement stock-info file indexer.
- [x] Implement stale-data scanner.
- [x] Implement rejected-stock 6-week cooldown checker.
- [x] Implement run manifest generation.
- [x] Implement run artifact persistence under `agents/runs/`.
- [x] Add deterministic provider tasks to weekly manifests.
- [x] Add dry-run-by-default provider task runner.
- [x] Add dry-run-by-default analysis task runner.
- [x] Add deterministic run summary generator.
- [x] Add deterministic quality report generator.
- [x] Add tests for file discovery, CSV validation, and manifest generation.

## Priority 3: Build Data Tools

- [x] Implement provider-neutral evidence packet schema.
- [x] Implement evidence packet JSON artifact writer.
- [x] Implement and live-smoke-test SEC EDGAR submissions and XBRL fetch tools.
- [x] Implement yfinance market data tool for prices and ratios.
- [x] Implement FMP market-data/fundamentals cross-check tool.
- [x] Implement Polygon/Massive U.S. ticker/OHLC cross-check tool.
- [x] Implement Alpha Vantage quote/overview cross-check tool.
- [x] Implement deterministic financial provider comparison step.
- [x] Implement Exa company, news, industry, and contents tools.
- [x] Add automatic Exa contents follow-up before company-news reviews.
- [x] Implement xAI Grok stock sentiment tool.
- [x] Implement xAI Grok industry sentiment/discovery tool.
- [x] Validate task-specific provider artifacts for same-subject Exa/Grok manifest tasks.
- [ ] Evaluate extra data providers: OpenBB, Twelve Data, EODHD, Finnhub, Nasdaq Data Link, FRED, ECB, Eurostat, Companies House, future ESMA ESAP.
- [ ] Add source normalization and citation utilities.
- [ ] Add tool guardrails for source metadata and secret redaction.

## Priority 4: Build Agents

- [x] Implement evidence packet schemas.
- [ ] Implement human request triage specialist.
- [x] Implement company news specialist.
- [x] Implement SDK SEC filing specialist.
- [x] Implement financial data specialist.
- [x] Implement SDK xAI Grok stock sentiment specialist.
- [ ] Implement xAI Grok industry sentiment specialist.
- [x] Implement Exa industry research specialist.
- [x] Implement discovery specialist.
- [ ] Implement tracked-stock alert specialist.
- [ ] Implement new-candidate discovery alert specialist.
- [x] Implement contradiction/risk specialist.
- [x] Implement SDK writer specialist for proposal drafting.
- [ ] Implement company file updater.
  - Current progress: approved SDK proposals can now be applied by `agent-runtime apply-proposal --proposal-id ORP-0001 --write`; SDK writer specialist can draft proposal-ready updates; broader updater behavior remains approval-gated and pending.
- [ ] Implement category state updater.
- [ ] Implement CSV updater.
- [x] Implement quality reviewer.

## Priority 5: Build Orchestration

- [x] Implement deterministic weekly runner.
  - Current progress: `python -m stock_research run-weekly` chains deterministic run steps through memory writer review and can optionally run scheduled SDK company-research fanout plus main orchestration.
- [ ] Implement OS/app scheduled execution.
  - Current progress: automatic Saturday invocation is still pending.
- [x] Implement deterministic Codex chat intake routing for user requests.
- [x] Implement market research sub-orchestrator.
  - Current progress: first SDK market-research sub-orchestrator exists for one industry/theme and includes Exa industry/company discovery, Grok/X discovery, candidate synthesis, and quality-review fanout. Manual candidate-review bridge now groups discovered leads and queues verification/monitoring decisions without moving stocks automatically. Scheduled market fanout is still pending.
- [x] Implement company research sub-orchestrator.
- [x] Implement portfolio review sub-orchestrator.
  - Current progress: first SDK version exists as `portfolio_review_orchestrator`; it reviews current holdings, monitoring, rejected cooldowns, open/approved HRQ items, and candidate verification results without applying writes.
- [x] Document human review operating model.
  - Current progress: `docs/descriptions/human_review_operating_model.md` defines `agents/human_review_digest.md` as the primary user inbox, `agents/human_review_queue.md` as durable state, deeper reports as drill-down context, async waiting behavior, and notification/email boundaries.
- [x] Implement memory/evaluation sub-orchestrator.
  - Current progress: first SDK version exists as `memory_evaluation_orchestrator`; it reviews telemetry, quality reports, memory reflection, recurring failures, memory update drafts, writer review, and finalization without applying memory writes.
- [x] Implement main orchestrator synthesis.
  - Current progress: first SDK main orchestrator exists as an opt-in API mode; final input aggregation now includes company, market, portfolio, memory/evaluation, candidate verification, and human-review surfaces. Default local scheduled/manual Codex flows now use Codex-supervised synthesis from `codex_supervised_review_pack.md`.
- [x] Implement human review queue writer.
- [x] Implement manual run manifest path for immediate user-requested research.
- [x] Implement final run summary.
- [x] Add tracing IDs and run metrics to artifacts.
- [x] Build OpenAI Agents SDK runtime foundation.
  - Current progress: first manual and opt-in API runtime slices implemented with dependency, runtime package, context/output contracts, registry, main orchestrator, company-research sub-orchestrator, company-news, company-search, financial, filing, sentiment, risk/thesis, writer, and quality-review specialists as tools, task-specific memory injection, repo/memory inspection tools, guarded provider/analysis SDK tools, prompt/spec files, run config, trace helpers, local SDK telemetry hooks, report/metrics artifacts, quality validation, tests, no-model-call smoke command, live manual `agent-runtime run --execute --write`, opt-in `run-weekly --write --execute-orchestrator`, and company-research fanout across current/monitoring tickers. Default local scheduled automation uses Codex-supervised synthesis without `--execute-orchestrator`.

## Priority 6: Learning Loop

- [x] Create `agents/memory/` conventions.
- [x] Add orchestrator lessons memory.
- [x] Add source quality memory.
- [x] Add specialist playbooks memory.
- [x] Add evaluation metrics memory.
- [x] Add memory index and deprecated memory.
- [x] Add agent memory workflow description.
- [x] Add deterministic memory loader, validator, summary, and task-context selector.
- [x] Add deterministic memory writer/update commands.
- [x] Add post-run reflection step.
- [x] Add automatic memory update proposal generation.
- [x] Add memory update draft/apply workflow.
- [x] Add prompt-ready memory context command for future specialist injection.
- [x] Build LLM memory writer agent.
- [x] Inject task-relevant memory context into specialist prompts from the orchestrator.
- [x] Add deterministic run finalization command.
- [x] Wire run finalization into scheduled/orchestrated runs.
- [x] Wire bounded memory writer review into scheduled/orchestrated runs.
- [x] Add recurring failure detection.

## Key Decisions Pending

- Data provider stack and budget.
- Human approval gates beyond the current digest-first queue/decision-writer model.
- Whether recommendations should be explicit or framed as research alerts.
- First stock universe to test.
- Priority European markets.
- Confidence scoring format.
- Provider source-of-truth hierarchy.

## Date-Stamped Updates

- 2026-04-30: Initial architecture plan created from user requirements and current repo scaffold.
- 2026-04-30: User confirmed US and Europe scope, alert + discovery goals, initial provider set, Saturday weekly cadence, and 6-week rejected-stock cooldown.
- 2026-04-30: Completed Priority 1 repo templates and file conventions.
- 2026-05-03: Added human-to-system intake layer with Codex chat as primary interface, human input queue, repo map, research priorities, and human review queue.
- 2026-05-03: Added stdlib-only `stock_research` deterministic core, CLI, README, SETUP, and unit tests.
- 2026-05-03: Added deterministic request router for human intake requests.
- 2026-05-03: Added provider-neutral source/evidence packet schema and evidence packet CLI.
- 2026-05-03: Added SEC EDGAR provider integration. Live use requires `SEC_USER_AGENT` or `--user-agent`, no API key.
- 2026-05-03: Live SEC smoke test passed for AAPL and wrote a validated evidence packet. Added compressed-response handling for SEC JSON responses.
- 2026-05-03: Added yfinance and Exa provider tools. Exa was implemented after reviewing the requested current Exa search/company/news/contents docs, with highlights-first search and separate contents extraction.
- 2026-05-03: Weekly manifests now include deterministic provider tasks for SEC, yfinance, and Exa. Added a provider task runner that dry-runs by default and can execute tasks explicitly.
- 2026-05-03: Replaced direct X.com recent search/counts with xAI Grok Responses API and built-in `x_search`, per user correction. Manifest provider tasks now include Grok X sentiment/news checks. Live AMD smoke test passed and wrote validated raw/evidence artifacts.
- 2026-05-03: Added FMP, Polygon/Massive, and Alpha Vantage provider tools after reviewing current official docs. They are wired into CLI, provider runner, and weekly manifests.
- 2026-05-04: Live AAPL smoke tests passed for FMP, Polygon/Massive, and Alpha Vantage. Added Alpha Vantage request spacing/retry for free-tier limits.
- 2026-05-04: Added `financial_compare` deterministic reconciliation step. It compares financial provider packets only, excludes Exa/Grok, writes raw comparison JSON plus a provider-neutral evidence packet, and is listed in weekly manifest `analysis_tasks`.
- 2026-05-04: Added structured operational agent memory under `agents/memory/`, plus `docs/descriptions/agent_memory_workflow.md` and `docs/templates/agent_memory_item_template.md`.
- 2026-05-04: Wired operational memory into deterministic tooling with `python -m stock_research memory summary`, `memory validate`, and `memory context --task TASK`; updated `AGENTS.md` to require operational memory loading before implementation.
- 2026-05-04: Clarified remaining learning-loop gaps: memory add/deprecate commands, automatic post-run reflection, memory update proposals, LLM memory writer agent, and orchestrator injection of memory context into specialist prompts.
- 2026-05-04: Implemented deterministic memory writer/update commands: `python -m stock_research memory add ...` and `python -m stock_research memory deprecate ...`, with validation tests.
- 2026-05-04: Implemented deterministic post-run reflection and memory update proposal generation with `python -m stock_research memory reflect-run --run-id RUN_ID [--write]`; wrote reflection artifacts for `agents/runs/2026-05-09_weekly/`.
- 2026-05-04: Implemented recurring failure detection with `python -m stock_research memory recurring-failures [--write]`; current real report has no recurring patterns yet because only one reflected run exists.
- 2026-05-04: Implemented deterministic run finalization with `python -m stock_research memory finalize-run --run-id RUN_ID`; it writes reflection, recurring-failure, and finalization artifacts but is not yet called automatically by a scheduler/orchestrator.
- 2026-05-05: User prioritized finishing the memory layer before adding another provider/specialist. Added memory update draft/apply tooling and prompt-ready memory context output so reflection proposals can become schema-valid reviewed memory updates and future specialists can receive ranked operational lessons.
- 2026-05-05: Added bounded LLM memory writer workflow with `memory writer-prompt` and `memory writer-review`. Live review can use OpenAI Responses API structured output via `OPENAI_API_KEY`, but operational memory writes still require deterministic `memory apply-updates`.
- 2026-05-05: Added deterministic weekly runner with `python -m stock_research run-weekly`. It chains manifest, provider tasks, analysis tasks, run summary, quality report, memory finalization, bounded memory-writer review, and orchestration report, then stops at the agent-framework decision boundary.
- 2026-05-04: Implemented the first deterministic financial-data specialist with `python -m stock_research financial review --ticker TICKER --run-id RUN_ID`; it consumes `financial_compare` packets and writes specialist evidence, raw review JSON, and markdown review artifacts.
- 2026-05-04: Implemented deterministic analysis-task runner with `python -m stock_research analysis-tasks --manifest PATH [--execute]`; it executes `financial_compare` and `financial_review` tasks from manifests in dependency order.
- 2026-05-04: Added AAPL as a monitoring workflow validation seed. Manifest planning, provider-task dry-run, analysis-task execution, run summary generation, quality report generation, and memory finalization were validated against the AAPL run artifacts.
- 2026-05-04: Fixed generated JSON handling and provider artifact naming. Generated run JSON/raw/evidence artifacts are ignored; Exa/Grok manifest tasks now use task-specific artifact ids; full AAPL weekly validation now finalizes as `complete` with zero quality findings.
- 2026-05-04: Added deterministic company-news specialist with `python -m stock_research news review --ticker TICKER --run-id RUN_ID`; weekly manifests now plan `company_news_review` analysis tasks.
- 2026-05-04: Re-reviewed official Exa search, search best-practice, company, news, contents, and contents best-practice docs. Confirmed `auto` + highlights as default, `category: "company"` only for company discovery, no news category parameter, and top-level `/contents` extraction parameters. Added `company_news_contents_follow_up` before `company_news_review`; headline/highlight-only news reviews now remain `partial_review`.
- 2026-05-03: Started SDK/framework review before agent runtime work. Current finding: Cursor SDK is likely a coding-agent automation adjunct, not the core stock-research orchestration runtime; OpenAI Agents SDK, Pydantic AI, and LangGraph remain the main candidates.
- 2026-05-06: User selected OpenAI Agents SDK as the framework. Created a dedicated SDK orchestration scratchpad and backlog. Next implementation slice is a small SDK runtime foundation with context, registry, guarded tools, structured outputs, tracing, memory injection, and one specialist-as-tool spike.
- 2026-05-06: Implemented the first OpenAI Agents SDK runtime foundation. Added `openai-agents`, `stock_research/agent_runtime/`, central registry, main orchestrator, company-news specialist-as-tool, typed context/output contracts, prompt/spec folders, smoke CLI, and tests. Live SDK orchestration is still pending.
- 2026-05-06: Added live manual SDK orchestration command and quality loop. The first live runs exposed missing/invalid memory ids and an invented company-file path; tools, prompt, and validation were tightened. The final AAPL live smoke completed with no quality findings and wrote runtime report, trace links, and metrics.
- 2026-05-06: Wired SDK orchestration into `run-weekly --write --execute-orchestrator`. Live scheduled test produced the expected `needs_review` result because provider/analysis tasks were dry-run while SDK output proposed AAPL file updates.
- 2026-05-06: Full fresh scheduled SDK run completed with providers, analysis, and orchestrator executed. Added generated-artifact cleanup before live execution after discovering stale smoke-test packets caused duplicate run-summary counts.
- 2026-05-07: Added deterministic SDK proposal bridge. `agent-runtime queue-proposals --write --queue-review` writes `orchestrator_update_proposals.md` and duplicate-safe human-review queue rows without editing company files.
- 2026-05-07: Added deterministic approved-proposal writer. `agent-runtime apply-proposal --proposal-id ORP-0001 --write` blocks unless the matching human-review row is `approved`, validates the target under `stock_tracking/stock_info_files/`, and writes source/change log updates plus `applied_update_proposals.md`.
- 2026-05-07: Hardened SDK repo/memory tools without adding CLI sprawl. Added function-first repo map, run summary, quality report, memory prompt context, and evidence packet index tools; runtime context now separates task-relevant memory ids from validator-known ids.
- 2026-05-07: Added guarded provider/analysis SDK function tools. The main orchestrator can now plan manifest provider and analysis tasks through tools, while live side effects are blocked unless runtime context grants execution.
- 2026-05-10: Added local SDK telemetry hooks. `run_metrics.md` now records agent lifecycle, tool calls, LLM calls/usage when available, injected operational memory ids, and final-output reported memory ids.
- 2026-05-10: Added SDK timeout/error policy and telemetry-informed memory reflection. SDK runtime failures now produce blocked reviewable artifacts, and post-run reflection reads `run_metrics.md` to surface timeout/error/missing-metrics issues.
- 2026-05-10: Added code-level SDK fanout infrastructure for future sub-orchestrators with per-task memory, timeout, partial-failure preservation, and aggregate metrics.
- 2026-05-10: Added first company-research SDK sub-orchestrator for one-ticker lane aggregation and company-news fanout.
- 2026-05-10: Added SDK financial specialist and wired it into main/company-research orchestrator tools plus company-research fanout. Financial synthesis still depends on deterministic `financial_compare` and financial review artifacts.
- 2026-05-10: Added SDK xAI/Grok stock sentiment specialist and wired it into main/company-research orchestrator tools plus company-research fanout. Sentiment synthesis uses Grok `x_search` artifacts as social signal only and now receives the active direct-X replacement memory.
- 2026-05-10: Added SDK SEC filing specialist and wired it into main/company-research orchestrator tools plus company-research fanout. Filing synthesis uses existing SEC EDGAR artifacts and does not assume European filing coverage.
- 2026-05-10: Added generic SDK Exa company-search specialist and deterministic Exa company-search provider planning for tracked tickers and human stock-research tickers. Per-ticker task ids are generated labels, not ticker-specific agents.
- 2026-05-10: Added generic SDK risk/thesis, writer, and quality-review specialists and wired them into main/company-research orchestrator tools plus company-research fanout.
- 2026-05-10: Wired scheduled `run-weekly --write --execute-orchestrator` to run per-ticker company-research fanout for all current-holding and monitoring tickers before the main orchestrator, writing per-ticker company-research markdown and metrics artifacts.
- 2026-05-16: Added robust Codex-supervised local automation mode. The scheduled command is now `C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis`; Python writes `codex_supervised_review_pack.md/json`, and Codex GPT-5.5 high writes `codex_supervised_review.md`. API SDK mode remains available for benchmark, debug, and remote/headless execution.
- 2026-05-10: Added first market-research SDK sub-orchestrator plus Exa industry, Grok/X discovery, and candidate discovery specialists. Discovery explicitly uses Grok/X for niche trends, hype, rumors, sentiment, and emerging ticker leads, while requiring Exa/filing/market-data verification before promotion.
- 2026-05-11: Completed the first manual discovery-to-monitoring lifecycle with `candidate-review`, `candidate-followup`, and approval-gated `candidate-promote`. Promotion now blocks unless a candidate is an approved and verified `monitoring_candidate` with required verification reports.
- 2026-05-11: Added open human-review digest. `human-review digest --write` writes `agents/human_review_digest.md` so the user can review pending approvals without scanning the raw queue table.
- 2026-05-11: Added deterministic human-review decision updater. `human-review decide --set HRQ-0004=approved --write` records explicit user decisions, appends decision notes, and refreshes the digest without running side-effect actions by itself.
- 2026-05-11: Approved HRQ-0007 for verification-only workflow validation. Provider/analysis verification ran for ADSE; promotion correctly remained blocked because this was not a `monitoring_candidate`. Added `candidate-verification-result` to consolidate missing provider evidence, specialist statuses, findings, and next actions.
- 2026-05-11: Implemented the first portfolio review sub-orchestrator. It is registered in the SDK runtime, exposed to the main orchestrator, and writes review packets/reports covering bucket state, open/approved HRQ items, candidate verification results, and next run tasks.
- 2026-05-11: Implemented the first memory/evaluation sub-orchestrator. It is registered in the SDK runtime, exposed to the main orchestrator, and writes learning-loop packets/reports from run metrics, quality reports, memory reflection, recurring failures, memory update drafts, memory writer review, and finalization.
- 2026-05-11: Broadened main orchestrator aggregation. Final synthesis prompts now receive a structured map of company research, market research, portfolio review, memory/evaluation, candidate verification, human-review digest, and review counts.
- 2026-05-11: Added human review operating model. The user-facing review inbox is `agents/human_review_digest.md`; reports such as portfolio review are deeper context. Runs should continue safe independent work asynchronously and leave only approval-gated branches waiting. Notification/email automation is planned later over the digest, with email initially notification-only.
