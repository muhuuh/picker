# Investment Agent Backlog

Last updated: 2026-05-03

## Purpose

This is the clear task backlog for building the stock tracking and investment research repo. It complements the longer architecture document in `docs/descriptions/investment_agent_workflow.md`.

## Confirmed Decisions

- Scope: US and Europe.
- Outputs: tracked-stock change alerts and new-stock discovery alerts.
- Initial approved providers: Exa, X.com, SEC, yfinance, FMP, Polygon, Alpha Vantage.
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
- [ ] Implement Exa tools.
  - Description: company news, industry research, market discovery.
- [ ] Implement X.com tools.
  - Description: stock sentiment and industry sentiment/discovery.
- [ ] Implement market data tools.
  - Description: yfinance first, then cross-check FMP, Polygon, and Alpha Vantage where configured.
- [ ] Evaluate additional sources.
  - Description: OpenBB, Twelve Data, EODHD, Finnhub, Nasdaq Data Link, FRED, ECB, Eurostat, Companies House, and future ESMA ESAP.

## Priority 4 Outputs

- `stock_research/evidence.py`
- `stock_research/providers/sec_edgar.py`
- `docs/descriptions/evidence_schema.md`
- `docs/descriptions/sec_edgar_provider.md`
- `python -m stock_research evidence new ...`
- `python -m stock_research evidence validate ...`
- `python -m stock_research sec company --ticker TICKER --run-id RUN_ID`
- `tests/test_evidence.py`
- `tests/test_sec_edgar_provider.py`
- Live SEC smoke artifact: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_sec_edgar_company_aapl.json`

## Priority 5: Specialist Agents

- [x] Define evidence packet schema.
  - Description: provider-neutral schema for all specialist outputs; currently implemented with stdlib dataclasses.
- [ ] Build company news specialist.
- [ ] Build SEC filing specialist.
- [ ] Build financial data specialist.
- [ ] Build X.com stock sentiment specialist.
- [ ] Build X.com industry sentiment specialist.
- [ ] Build Exa industry research specialist.
- [ ] Build discovery specialist.
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
  - Description: run weekly Saturday by default and support manual runs from the human input queue.
- [ ] Build company research sub-orchestrator.
  - Description: coordinates filings, news, financials, sentiment, and risk checks for one ticker.
- [ ] Build market research sub-orchestrator.
  - Description: coordinates industry, macro, theme, and candidate discovery.
- [ ] Build portfolio review sub-orchestrator.
  - Description: assesses impact across current holdings, monitoring, and rejected buckets.
- [ ] Build memory and evaluation sub-orchestrator.
  - Description: extracts lessons from traces and quality reports.
- [ ] Build main orchestrator.
  - Description: synthesizes all evidence, chooses updates, creates alerts, incorporates human input queue items, and prepares next actions.
- [ ] Build human review queue.
  - Description: collects moves, strategy changes, and high-impact recommendations for user approval.

## Priority 7: Learning Loop

- [ ] Create `agents/memory/`.
  - Description: dedicated agent operational memory separate from investment memory.
- [ ] Create `orchestrator_lessons.md`.
  - Description: routing mistakes, prompt improvements, failed assumptions.
- [ ] Create `source_quality.md`.
  - Description: source reliability, provider gaps, duplicate/noisy sources.
- [ ] Create `specialist_playbooks.md`.
  - Description: best instructions and gotchas per specialist type.
- [ ] Create `evaluation_metrics.md`.
  - Description: run duration, tool failures, stale-data fixes, citation quality, false positives.
- [ ] Add post-run reflection.
  - Description: after each run, update memory with lessons and next-run improvements.

## Open Decisions

- Priority European markets: all major European exchanges or start with UK, Germany, France, Netherlands, Nordics, Switzerland?
- Confidence format: numeric score, low/medium/high, or evidence-grade rubric?
- Provider source-of-truth hierarchy when metrics conflict.
- Human approval gates for file writes, stock movement, and strategy changes.
- First test stock universe.
- Agent SDK/framework choice: OpenAI Agents SDK, Pydantic AI, LangGraph, Cursor SDK, or a hybrid approach.
