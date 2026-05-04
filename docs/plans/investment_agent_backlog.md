# Investment Agent Backlog

Last updated: 2026-05-04

## Purpose

This is the clear task backlog for building the stock tracking and investment research repo. It complements the longer architecture document in `docs/descriptions/investment_agent_workflow.md`.

## Confirmed Decisions

- Scope: US and Europe.
- Outputs: tracked-stock change alerts and new-stock discovery alerts.
- Initial approved providers: Exa, xAI/Grok, SEC, yfinance, FMP, Polygon, Alpha Vantage.
- Schedule: weekly deep research on Saturday.
- Review rhythm: user reviews results on Sunday and plans the next week.
- Rejected-stock rule: do not resurface rejected stocks for 6 weeks unless the user overrides it.
- Human interface: Codex chat is the primary interface; proactive user requests go to a human input queue and system approval items go to a separate human review queue.

## Priority 0: Lock Product Shape

- [x] Create initial architecture description.
  - Description: explain folder model, agent layers, deterministic kickoff, specialists, memory, and guardrails.
  - Output: `docs/descriptions/investment_agent_workflow.md`.
- [x] Record durable user decisions.
  - Description: store scope, cadence, providers, alert goals, rejected cooldown.
  - Output: `MEMORY.md`, architecture doc, scratchpad.
- [x] Add human-to-system intake design.
  - Description: define how Codex chat input becomes durable repo state and future automated research input.
  - Output: `docs/descriptions/human_interaction_workflow.md`, `docs/descriptions/repo_map.md`, `docs/plans/human_research_requests.md`, `strategy/research_priorities.md`, `agents/human_review_queue.md`.
- [ ] Validate final architecture with user.
  - Description: review the flow and decide whether any agent roles or memory surfaces are missing.
  - Output: updated architecture doc and this backlog.
- [x] Choose first build slice.
  - Description: pick the first thin vertical slice, preferably file templates plus deterministic repo loader.
  - Output: first slice chosen as repo templates and file conventions.

## Priority 1: Repo File System and Templates

- [x] Create category CSV schemas.
  - Description: define standard columns for `current_holdings`, `monitoring`, and `rejected`.
  - Suggested columns: ticker, company_name, exchange, country, sector, industry, status, source, price, currency, market_cap, pe_ratio, date_found, date_last_updated, next_review_date, stock_info_file, notes.
  - Extra rejected columns: date_rejected, reject_reason, next_eligible_review_date.
- [x] Create category state markdown templates.
  - Description: holdings, monitoring, and rejected each need a living state file with findings, risks, plans, and changes.
- [x] Create company markdown template.
  - Description: detailed per-company file with thesis, filings, financials, developments, sentiment, risks, open questions, next actions, and change log.
- [x] Create strategy starter files.
  - Description: `investment_strategy.md`, `screening_criteria.md`, and `risk_rules.md`.
- [x] Create market research folder conventions.
  - Description: standard structure for industries, themes, macro, and discovery.

## Priority 1 Outputs

- `stock_tracking/current_holdings/current_holdings.csv`
- `stock_tracking/current_holdings/current_holdings_state.md`
- `stock_tracking/monitoring/monitoring.csv`
- `stock_tracking/monitoring/monitoring_state.md`
- `stock_tracking/rejected/rejected.csv`
- `stock_tracking/rejected/rejected_state.md`
- `stock_tracking/stock_info_files/README.md`
- `docs/templates/company_stock_info_template.md`
- `docs/templates/category_state_template.md`
- `docs/templates/stock_tracking_csv_schema.md`
- `strategy/investment_strategy.md`
- `strategy/screening_criteria.md`
- `strategy/risk_rules.md`
- `strategy/research_priorities.md`
- `market_research/README.md`

## Priority 2: Human Interaction Layer

- [x] Create human interaction workflow description.
  - Description: document how Codex chat requests are classified and routed.
- [x] Create repo map.
  - Description: quick navigation map for Codex, orchestrator, and future agents.
- [x] Create human input queue.
  - Description: durable queue for proactive user requests.
- [x] Create research priorities file.
  - Description: persistent recurring topics for future discovery and market research.
- [x] Create human review queue.
  - Description: separate approval queue for system-generated decisions.
- [x] Implement human request classifier.
  - Description: classify user requests into stock research, industry research, theme tracking, strategy change, alert review, manual run, stock status move, or other.
- [x] Implement request router.
  - Description: update the right repo artifact based on request type.
- [x] Implement human input queue loader.
  - Description: deterministic core reads `docs/plans/human_research_requests.md` and includes queued items in run manifests.
- [x] Implement research priorities loader.
  - Description: deterministic core reads `strategy/research_priorities.md` before market discovery.
- [x] Implement human review queue writer.
  - Description: orchestrator and quality reviewer can add approval items without mixing them into the input queue.
- [x] Implement manual run manifest path.
  - Description: allow Codex to create one-off manual run manifests under `agents/runs/YYYY-MM-DD_manual-*`.

## Priority 2 Outputs

- `python -m stock_research route-request "..."`
- Stock requests can create monitoring CSV rows and company stubs.
- Industry/theme requests can create market research files and research priority rows.
- Strategy/status move requests can create human review queue items.
- Manual run requests can create manual run manifests.

## Priority 3: Deterministic Core

- [x] Implement repo state loader.
  - Description: read CSVs, category state files, company files, strategy files, scratchpads, plan files, and memory.
- [x] Implement schema validator.
  - Description: validate CSV columns, dates, paths, status values, and cooldown fields.
- [x] Implement stale-data scanner.
  - Description: detect old company files, stale prices, missing filing checks, and old category state.
- [x] Implement rejected cooldown checker.
  - Description: suppress rejected candidates until 6 weeks after rejection.
- [x] Implement weekly run manifest.
  - Description: generate Saturday run plan with tracked stocks, industries, providers, human input queue items, research priorities, tasks, and expected outputs.
- [x] Implement run artifact storage.
  - Description: save each run under `agents/runs/YYYY-MM-DD_run-id/`.
- [x] Implement analysis task runner.
  - Description: dry-run or execute deterministic post-provider analysis tasks from a manifest.
- [x] Implement deterministic run summary generator.
  - Description: write run_summary artifacts from manifest, evidence packets, and financial review reports.
- [x] Implement deterministic quality report generator.
  - Description: write quality_report artifacts with evidence validation and missing planned-provider packet findings.

## Priority 3 Outputs

- `stock_research/`: deterministic Python package.
- `python -m stock_research summary`
- `python -m stock_research validate`
- `python -m stock_research stale`
- `python -m stock_research manifest`
- `python -m stock_research classify-request "..."`
- `python -m stock_research add-request "..."`
- `README.md`
- `SETUP.md`
- `tests/`

## Priority 4: Provider and Tool Layer

- [x] Implement source normalization and evidence packet schema.
  - Description: every provider result becomes a consistent source object with URL, publisher, date, accessed_at, provider, and confidence notes.
- [x] Implement evidence packet artifact writer.
  - Description: store provider-neutral evidence packets under `agents/runs/{run_id}/evidence_packets/`.
- [x] Implement SEC EDGAR tool.
  - Description: US filings, submissions, and XBRL facts. Live AAPL smoke test passed on 2026-05-03.
- [x] Implement Exa tools.
  - Description: company news, industry research, market discovery, and content extraction. Implemented as deterministic provider tools first, to be wrapped by specialists later. Manifest-driven artifacts use task-specific names so multiple searches for one subject do not overwrite each other.
- [x] Wire default Exa tasks into weekly deterministic kickoff.
  - Description: holdings/monitoring use Exa news; research priorities use Exa industry/general; discovery uses Exa company; human input queue items route to the relevant Exa modes; high-value results use Exa contents.
- [x] Implement xAI/Grok X research tools.
  - Description: stock sentiment, industry sentiment, latest X news, and discovery support through Grok `x_search` using `XAI_API_KEY`. Manifest-driven artifacts use task-specific names and retry slow `x_search` responses once.
- [ ] Add Grok model selection optimization.
  - Description: keep `grok-4.3` as the current conservative default, but later add deterministic model-tier routing such as a faster Grok model for low-priority/simple X scans and `grok-4.3` for high-priority holdings, user-requested research, candidate discovery, and complex sentiment synthesis.
- [x] Implement market data tools.
  - Description: yfinance, FMP, Polygon/Massive, and Alpha Vantage are implemented. FMP/Polygon/Alpha live AAPL smoke tests passed on 2026-05-04.
- [x] Implement financial data comparison layer.
  - Description: deterministic reconciliation of yfinance/FMP/Polygon/Massive/Alpha/SEC financial packets into a single `financial_compare` evidence packet before LLM synthesis.
- [ ] Evaluate additional sources.
  - Description: OpenBB, Twelve Data, EODHD, Finnhub, Nasdaq Data Link, FRED, ECB, Eurostat, Companies House, and future ESMA ESAP.

## Priority 4 Outputs

- `stock_research/evidence.py`
- `stock_research/providers/sec_edgar.py`
- `stock_research/providers/exa.py`
- `stock_research/providers/xai_grok.py`
- `stock_research/providers/yfinance_provider.py`
- `stock_research/providers/fmp.py`
- `stock_research/providers/polygon_provider.py`
- `stock_research/providers/alpha_vantage.py`
- `stock_research/financial_compare.py`
- `stock_research/financial_specialist.py`
- `stock_research/company_news_specialist.py`
- `stock_research/analysis_runner.py`
- `stock_research/run_summary.py`
- `stock_research/quality_report.py`
- `stock_research/provider_runner.py`
- `docs/descriptions/evidence_schema.md`
- `docs/descriptions/sec_edgar_provider.md`
- `docs/descriptions/exa_provider.md`
- `docs/descriptions/xai_grok_provider.md`
- `docs/descriptions/yfinance_provider.md`
- `docs/descriptions/fmp_provider.md`
- `docs/descriptions/polygon_provider.md`
- `docs/descriptions/alpha_vantage_provider.md`
- `docs/descriptions/financial_compare.md`
- `docs/descriptions/financial_data_specialist.md`
- `docs/descriptions/company_news_specialist.md`
- `python -m stock_research evidence new ...`
- `python -m stock_research evidence validate ...`
- `python -m stock_research sec company --ticker TICKER --run-id RUN_ID`
- `python -m stock_research yfinance company --ticker TICKER --run-id RUN_ID`
- `python -m stock_research fmp company --ticker TICKER --run-id RUN_ID`
- `python -m stock_research polygon company --ticker TICKER --run-id RUN_ID`
- `python -m stock_research alpha-vantage company --ticker TICKER --run-id RUN_ID`
- `python -m stock_research financial compare --ticker TICKER --run-id RUN_ID`
- `python -m stock_research financial review --ticker TICKER --run-id RUN_ID`
- `python -m stock_research news contents-follow-up --ticker TICKER --run-id RUN_ID`
- `python -m stock_research news review --ticker TICKER --run-id RUN_ID`
- `python -m stock_research exa search --query QUERY --subject-type TYPE --subject-id ID --run-id RUN_ID`
- `python -m stock_research exa contents --url URL --subject-type TYPE --subject-id ID --run-id RUN_ID`
- `python -m stock_research xai x-search --ticker TICKER --subject-type company --subject-id TICKER --run-id RUN_ID`
- `python -m stock_research provider-tasks --manifest PATH`
- `python -m stock_research provider-tasks --manifest PATH --execute`
- `python -m stock_research analysis-tasks --manifest PATH`
- `python -m stock_research analysis-tasks --manifest PATH --execute`
- `tests/test_analysis_runner.py`
- `python -m stock_research run-summary --run-id RUN_ID --write`
- `python -m stock_research quality-report --run-id RUN_ID --write`
- `tests/test_run_summary.py`
- `tests/test_quality_report.py`
- Generated run JSON, raw provider JSON, evidence packet JSON, and generated recurring-failure JSON are ignored; markdown summaries/reports/finalization files are the reviewable artifacts.
- `tests/test_evidence.py`
- `tests/test_sec_edgar_provider.py`
- `tests/test_exa_provider.py`
- `tests/test_xai_grok_provider.py`
- `tests/test_yfinance_provider.py`
- `tests/test_fmp_provider.py`
- `tests/test_polygon_provider.py`
- `tests/test_alpha_vantage_provider.py`
- `tests/test_financial_compare.py`
- `tests/test_financial_specialist.py`
- `tests/test_company_news_specialist.py`
- `tests/test_provider_runner.py`
- `tests/test_memory.py`
- Live SEC smoke artifact: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_sec_edgar_company_aapl.json`
- Live xAI Grok smoke artifact: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_xai_grok_company_amd.json`
- Live FMP smoke artifact: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_fmp_company_aapl.json`
- Live Polygon/Massive smoke artifact: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_polygon_company_aapl.json`
- Live Alpha Vantage smoke artifact: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_alpha_vantage_company_aapl.json`
- Live financial compare smoke artifact: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_financial_compare_company_aapl.json`
- Written weekly manifest with provider tasks: `agents/runs/2026-05-09_weekly/manifest.json`

## Priority 5: Specialist Agents

- [x] Define evidence packet schema.
  - Description: provider-neutral schema for all specialist outputs; currently implemented with stdlib dataclasses.
- [x] Build company news specialist.
  - Description: deterministic first company-news specialist consumes Exa company-news packets plus contents follow-up, writes specialist evidence, raw review JSON, and markdown review.
- [x] Add automatic Exa contents follow-up for company news.
  - Description: manifests now plan `company_news_contents_follow_up` before `company_news_review`; search-highlight-only reviews remain `partial_review` until Exa contents confirms selected URLs.
- [ ] Build SEC filing specialist.
- [x] Build financial data specialist.
  - Description: deterministic first specialist that consumes `financial_compare` packets, writes a specialist evidence packet, raw review JSON, and markdown financial review. Future LLM version can extend this surface without changing the input/output contract.
- [ ] Build xAI Grok stock sentiment specialist.
- [ ] Build xAI Grok industry sentiment specialist.
- [ ] Build Exa industry research specialist.
  - Description: should choose Exa `industry`, `news`, `general`, `company`, and `contents` based on the research goal.
- [ ] Build discovery specialist.
  - Description: should use Exa `company` for candidate discovery and Exa `general` for context/validation.
- [ ] Build tracked-stock alert specialist.
- [ ] Build new-candidate discovery alert specialist.
- [ ] Build contradiction and risk specialist.
- [ ] Build human request triage specialist.
- [ ] Build company file updater.
- [ ] Build category state updater.
- [ ] Build CSV updater.
- [ ] Build quality reviewer.

## Priority 6: Orchestration

- [ ] Build scheduled runner.
  - Description: run weekly Saturday by default and support manual runs from the human input queue. Current progress: deterministic manifests, provider-task execution, and run finalization exist; OS/app scheduling and full orchestration still pending.
- [ ] Build company research sub-orchestrator.
  - Description: coordinates filings, news, financials, sentiment, and risk checks for one ticker.
- [ ] Build market research sub-orchestrator.
  - Description: coordinates industry, macro, theme, and candidate discovery.
- [ ] Build portfolio review sub-orchestrator.
  - Description: assesses impact across current holdings, monitoring, and rejected buckets.
- [ ] Build memory and evaluation sub-orchestrator.
  - Description: extracts lessons from traces, run summaries, quality reports, provider failures, and user corrections.
- [ ] Build main orchestrator.
  - Description: synthesizes all evidence, chooses updates, creates alerts, incorporates human input queue items, and prepares next actions.
- [ ] Inject operational memory into specialist prompts.
  - Description: orchestrator should call `python -m stock_research memory context --task TASK` or the equivalent Python function and pass the relevant lessons into each specialist prompt before execution.
- [ ] Build human review queue.
  - Description: collects moves, strategy changes, and high-impact recommendations for user approval.

## Priority 7: Learning Loop

- [x] Create `agents/memory/`.
  - Description: dedicated agent operational memory separate from investment memory.
- [x] Create `orchestrator_lessons.md`.
  - Description: routing mistakes, prompt improvements, failed assumptions.
- [x] Create `source_quality.md`.
  - Description: source reliability, provider gaps, duplicate/noisy sources.
- [x] Create `specialist_playbooks.md`.
  - Description: best instructions and gotchas per specialist type.
- [x] Create `evaluation_metrics.md`.
  - Description: run duration, tool failures, stale-data fixes, citation quality, false positives.
- [x] Create memory index and deprecated memory.
  - Description: give future agents a memory entry point and a place to preserve superseded/wrong lessons.
- [x] Document agent memory workflow.
  - Description: define read flow, write flow, lifecycle fields, and guardrails.
- [x] Add deterministic memory loader and validator.
  - Description: expose `memory summary`, `memory validate`, and `memory context --task TASK` commands so Codex and future orchestrators can inspect task-relevant memory.
- [x] Add deterministic memory writer/update commands.
  - Description: implement safe commands such as `python -m stock_research memory add ...` and `python -m stock_research memory deprecate ...` so memory updates are schema-valid and auditable.
- [x] Add post-run reflection.
  - Description: after each weekly/manual run, read run summary, quality report, provider failures, user corrections, and trace references to identify learning candidates.
- [x] Add automatic memory update proposals.
  - Description: generate proposed add/update/deprecate actions after reflection, with evidence links and confidence, before applying them.
- [ ] Build LLM memory writer agent.
  - Description: bounded specialist that converts reflection findings into concise memory items; it should not write freely without schema validation and should send high-impact changes to human review.
- [x] Add recurring failure detection.
  - Description: detect repeated provider failures, noisy alerts, missing citations, bad routing, and repeated user corrections across runs.
- [x] Add deterministic run finalization command.
  - Description: write post-run reflection, recurring-failure reports, and finalization artifacts with one command for future scheduler/orchestrator use.
- [ ] Wire run finalization into scheduled/orchestrated runs.
  - Description: call `python -m stock_research memory finalize-run --run-id RUN_ID` automatically after provider tasks, analysis tasks, run summary, and quality report generation.

## Open Decisions

- Priority European markets: all major European exchanges or start with UK, Germany, France, Netherlands, Nordics, Switzerland?
- Confidence format: numeric score, low/medium/high, or evidence-grade rubric?
- Provider source-of-truth hierarchy when metrics conflict.
- Human approval gates for file writes, stock movement, and strategy changes.
- First test stock universe.
- Agent SDK/framework choice: OpenAI Agents SDK, Pydantic AI, LangGraph, Cursor SDK, or a hybrid approach.
- First stock universe to test beyond the current smoke-test artifacts.
