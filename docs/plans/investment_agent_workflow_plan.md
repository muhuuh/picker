# Investment Agent Workflow Plan

Last updated: 2026-05-04

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
- [ ] Implement SEC filing specialist.
- [x] Implement financial data specialist.
- [ ] Implement xAI Grok stock sentiment specialist.
- [ ] Implement xAI Grok industry sentiment specialist.
- [ ] Implement Exa industry research specialist.
- [ ] Implement discovery specialist.
- [ ] Implement tracked-stock alert specialist.
- [ ] Implement new-candidate discovery alert specialist.
- [ ] Implement contradiction/risk specialist.
- [ ] Implement company file updater.
- [ ] Implement category state updater.
- [ ] Implement CSV updater.
- [ ] Implement quality reviewer.

## Priority 5: Build Orchestration

- [ ] Implement scheduled runner.
  - Current progress: deterministic manifests, provider-task execution, and run finalization command exist; actual scheduled/orchestrated invocation is still pending.
- [x] Implement deterministic Codex chat intake routing for user requests.
- [ ] Implement market research sub-orchestrator.
- [ ] Implement company research sub-orchestrator.
- [ ] Implement portfolio review sub-orchestrator.
- [ ] Implement main orchestrator synthesis.
- [x] Implement human review queue writer.
- [x] Implement manual run manifest path for immediate user-requested research.
- [x] Implement final run summary.
- [ ] Add tracing IDs and run metrics to artifacts.

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
- [ ] Build LLM memory writer agent.
- [ ] Inject task-relevant memory context into specialist prompts from the orchestrator.
- [x] Add deterministic run finalization command.
- [ ] Wire run finalization into scheduled/orchestrated runs.
- [x] Add recurring failure detection.

## Key Decisions Pending

- Data provider stack and budget.
- Agent SDK/framework choice for Priority 4 and Priority 5 implementation.
- Human approval gates.
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
- 2026-05-04: Implemented the first deterministic financial-data specialist with `python -m stock_research financial review --ticker TICKER --run-id RUN_ID`; it consumes `financial_compare` packets and writes specialist evidence, raw review JSON, and markdown review artifacts.
- 2026-05-04: Implemented deterministic analysis-task runner with `python -m stock_research analysis-tasks --manifest PATH [--execute]`; it executes `financial_compare` and `financial_review` tasks from manifests in dependency order.
- 2026-05-04: Added AAPL as a monitoring workflow validation seed. Manifest planning, provider-task dry-run, analysis-task execution, run summary generation, quality report generation, and memory finalization were validated against the AAPL run artifacts.
- 2026-05-04: Fixed generated JSON handling and provider artifact naming. Generated run JSON/raw/evidence artifacts are ignored; Exa/Grok manifest tasks now use task-specific artifact ids; full AAPL weekly validation now finalizes as `complete` with zero quality findings.
- 2026-05-04: Added deterministic company-news specialist with `python -m stock_research news review --ticker TICKER --run-id RUN_ID`; weekly manifests now plan `company_news_review` analysis tasks.
- 2026-05-04: Re-reviewed official Exa search, search best-practice, company, news, contents, and contents best-practice docs. Confirmed `auto` + highlights as default, `category: "company"` only for company discovery, no news category parameter, and top-level `/contents` extraction parameters. Added `company_news_contents_follow_up` before `company_news_review`; headline/highlight-only news reviews now remain `partial_review`.
- 2026-05-03: Started SDK/framework review before agent runtime work. Current finding: Cursor SDK is likely a coding-agent automation adjunct, not the core stock-research orchestration runtime; OpenAI Agents SDK, Pydantic AI, and LangGraph remain the main candidates.
