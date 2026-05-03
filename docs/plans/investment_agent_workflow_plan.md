# Investment Agent Workflow Plan

Last updated: 2026-05-03

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
- [x] Add tests for file discovery, CSV validation, and manifest generation.

## Priority 3: Build Data Tools

- [x] Implement provider-neutral evidence packet schema.
- [x] Implement evidence packet JSON artifact writer.
- [x] Implement and live-smoke-test SEC EDGAR submissions and XBRL fetch tools.
- [x] Implement yfinance market data tool for prices and ratios.
- [x] Implement Exa company, news, industry, and contents tools.
- [ ] Implement X.com stock sentiment tool.
- [ ] Implement X.com industry sentiment/discovery tool.
- [ ] Evaluate extra data providers: OpenBB, Twelve Data, EODHD, Finnhub, Nasdaq Data Link, FRED, ECB, Eurostat, Companies House, future ESMA ESAP.
- [ ] Add source normalization and citation utilities.
- [ ] Add tool guardrails for source metadata and secret redaction.

## Priority 4: Build Agents

- [x] Implement evidence packet schemas.
- [ ] Implement human request triage specialist.
- [ ] Implement company news specialist.
- [ ] Implement SEC filing specialist.
- [ ] Implement financial data specialist.
- [ ] Implement X.com stock sentiment specialist.
- [ ] Implement X.com industry sentiment specialist.
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
- [x] Implement deterministic Codex chat intake routing for user requests.
- [ ] Implement market research sub-orchestrator.
- [ ] Implement company research sub-orchestrator.
- [ ] Implement portfolio review sub-orchestrator.
- [ ] Implement main orchestrator synthesis.
- [x] Implement human review queue writer.
- [x] Implement manual run manifest path for immediate user-requested research.
- [ ] Implement final run summary.
- [ ] Add tracing IDs and run metrics to artifacts.

## Priority 6: Learning Loop

- [ ] Create `agents/memory/` conventions.
- [ ] Add orchestrator lessons memory.
- [ ] Add source quality memory.
- [ ] Add specialist playbooks memory.
- [ ] Add evaluation metrics memory.
- [ ] Add post-run reflection step.
- [ ] Add recurring failure detection.

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
- 2026-05-03: Started SDK/framework review before agent runtime work. Current finding: Cursor SDK is likely a coding-agent automation adjunct, not the core stock-research orchestration runtime; OpenAI Agents SDK, Pydantic AI, and LangGraph remain the main candidates.
