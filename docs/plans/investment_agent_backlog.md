# Investment Agent Backlog

Last updated: 2026-05-11

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
- Agent framework: OpenAI Agents SDK.

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
- [x] Select agent orchestration framework.
  - Description: user selected OpenAI Agents SDK; dedicated scratchpad/backlog now track the runtime implementation.
  - Output: `docs/scratchpads/openai_agents_sdk_orchestration_scratchpad.md`, `docs/plans/openai_agents_sdk_orchestration_backlog.md`.
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
- [x] Document human review operating model.
  - Description: define the digest-first review inbox, async waiting behavior, portfolio-review audience, notification policy, and approval-gated follow-up rules.
  - Output: `docs/descriptions/human_review_operating_model.md`.
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
- [x] Build SEC filing specialist.
  - Description: SDK filing specialist consumes SEC EDGAR artifacts and is included in company-research fanout. European filing coverage still needs future providers.
- [x] Build financial data specialist.
  - Description: deterministic first specialist that consumes `financial_compare` packets, writes a specialist evidence packet, raw review JSON, and markdown financial review. Future LLM version can extend this surface without changing the input/output contract.
- [x] Build xAI Grok stock sentiment specialist.
  - Description: SDK sentiment specialist consumes xAI/Grok `x_search` artifacts as social-signal evidence and is included in company-research fanout.
- [x] Build xAI Grok industry sentiment specialist.
  - Description: SDK Grok discovery specialist consumes xAI/Grok `x_search` industry/theme artifacts for X narratives, hype, rumors, sentiment, and emerging ticker leads. Grok output remains social-signal lead generation until verified.
- [x] Build Exa industry research specialist.
  - Description: should choose Exa `industry`, `news`, `general`, `company`, and `contents` based on the research goal.
- [x] Build discovery specialist.
  - Description: should use Exa `company` for candidate discovery and Exa `general` for context/validation.
- [ ] Build tracked-stock alert specialist.
- [x] Build new-candidate discovery alert specialist.
  - Description: first candidate discovery schema and quality gates are implemented for manual market research. Candidate leads track ticker/company, source channels, verification status, hype level, rejected cooldown status, and next action.
- [x] Build contradiction and risk specialist.
  - Description: SDK risk/thesis specialist is included in company-research fanout and reviews thesis impact, contradictions, and risk deltas from the aggregated packet.
- [ ] Build human request triage specialist.
- [ ] Build company file updater.
  - Current progress: deterministic approved-proposal writer exists for SDK proposals with `agent-runtime apply-proposal --proposal-id ORP-0001 --write`; SDK writer specialist now drafts proposal-ready updates inside company-research fanout. Broader automatic company-file update strategy is still approval-gated and pending.
- [ ] Build category state updater.
- [ ] Build CSV updater.
- [x] Build quality reviewer.
  - Description: SDK quality-review specialist is included in company-research fanout for citation/source/approval-gate checks.

## Priority 6: Orchestration

- [x] Build deterministic weekly runner.
  - Description: `python -m stock_research run-weekly` now chains manifest generation, provider tasks, analysis tasks, run summary, quality report, memory finalization, bounded memory-writer review, optional SDK orchestration, and orchestration report. Live provider/analysis execution cleans generated run artifacts first to avoid stale duplicate packets on reruns.
- [x] Build OpenAI Agents SDK runtime foundation.
  - Description: implement the dedicated SDK runtime backlog with context, registry, guarded tools, structured outputs, tracing, memory injection, and one specialist-as-tool spike.
  - Current progress: first manual runtime slice is implemented and live-smoke-tested with no quality findings after prompt/tool/validator tightening. `run-weekly --write --execute-orchestrator` is implemented as an opt-in scheduled SDK path, with freshness gating when provider/analysis tasks are dry-run. Full fresh `--execute-providers --execute-analysis --execute-orchestrator` validation completed with no findings after adding generated-artifact cleanup. SDK proposals now flow through `agent-runtime queue-proposals --write --queue-review`, approved individual proposals can be applied through `agent-runtime apply-proposal`, repo/memory inspection tools now wrap Python functions directly with task-specific memory injection, guarded provider/analysis SDK tools plan by default while blocking live side effects unless runtime context grants execution, local SDK hooks now record agent/tool/LLM telemetry plus injected/reported memory ids, SDK timeouts/errors now return blocked reviewable artifacts, memory reflection now reads SDK run metrics, code-level fanout infrastructure exists for sub-orchestrators, and scheduled company-research fanout now runs across current-holding and monitoring tickers with financial, company-news, Exa company-search, SEC filing, sentiment, risk/thesis, writer, and quality-review specialist lanes.
  - Output: `stock_research/agent_runtime/`, `docs/descriptions/openai_agents_sdk_orchestration.md`, tests, `python -m stock_research agent-runtime smoke`, and `python -m stock_research agent-runtime run --run-id RUN_ID --execute --write`.
- [ ] Build OS/app scheduled execution.
  - Description: run the deterministic weekly runner automatically on Saturday and support manual trigger flows.
- [x] Build open human-review digest.
  - Description: create a concise report/command that summarizes only open `agents/human_review_queue.md` items, grouped by decision type and priority, with each item showing the HRQ id, ticker/company, recommended user action, confidence/verification status, and link to the deeper evidence artifact.
  - Purpose: the user should not need to manually scan the full markdown table to find what needs attention.
  - Current command: `python -m stock_research human-review digest --write`.
  - Current output: `agents/human_review_digest.md`.
- [x] Build deterministic human-review decision updater.
  - Description: record explicit user decisions on HRQ rows without triggering side effects directly.
  - Current command: `python -m stock_research human-review decide --set HRQ-0004=approved --note "Run verification." --write`.
  - Current behavior: updates `agents/human_review_queue.md`, appends a decision note, refreshes `agents/human_review_digest.md`, and leaves follow-up verification, proposal application, stock moves, or monitoring promotion to separate approval-gated commands.
- [ ] Add review notification automation.
  - Description: after weekly/manual runs, have Codex/app automation summarize new or high-priority open review items and notify the user by app notification and/or email when there are interesting findings or approvals needed.
  - Rule: notifications summarize `agents/human_review_digest.md`; they are not approvals.
  - Future option: evaluate strict Gmail reply ingestion only after digest quality is stable, with duplicate detection, identity checks, and deterministic decision writing.
  - Timing: implement after the manual review digest is reliable and after the scheduled/manual run flow is stable enough to avoid noisy alerts.
- [ ] Add run-end review digest summary.
  - Description: every manual/weekly run should finish by refreshing or summarizing `agents/human_review_digest.md`, including new high-priority items and what the human can decide next.
  - Reason: the user should not need to remember to open review files manually.
- [x] Build company research sub-orchestrator.
  - Description: coordinates filings, news, financials, sentiment, and risk checks for one ticker.
  - Current progress: first SDK version registered as `company_research_orchestrator`; it builds a one-ticker lane packet, uses financial, company-news, company-search, filing, sentiment, risk/thesis, writer, and quality-review fanout, writes per-ticker scheduled artifacts, and aggregates partial results into next-run tasks.
- [x] Build market research sub-orchestrator.
  - Description: coordinates industry, macro, theme, and candidate discovery.
  - Current progress: first SDK market-research sub-orchestrator is implemented with Exa industry, Grok/X discovery, candidate discovery, and quality-review fanout. A clean manual run path now exists through `python -m stock_research market-research run --topic TOPIC --subject-type industry|theme --write [--execute-providers] [--execute-orchestrator]`, which writes a market report plus candidate lead artifacts and applies discovery quality gates. `market-research candidate-review --run-id RUN_ID --write --queue-review` now groups duplicate/share-class leads and creates human-review decisions for verification or possible monitoring without moving stocks automatically. Scheduled run-weekly integration is intentionally deferred until manual iteration quality is good.
- [ ] Complete the market discovery lifecycle.
  - Description: split discovery into explicit phases so leads do not get confused with verified monitoring candidates.
  - Phase 1 - Discover: Exa and Grok/X surface industries, themes, companies, tickers, hype, rumors, and community sentiment.
  - Phase 2 - Normalize: resolve company name, ticker, exchange, country, duplicate listings, and share-class variants.
  - Phase 3 - Gate: apply source-id, Grok-only, rumor, verification, strategy-fit, and rejected-cooldown rules.
  - Phase 4 - Human review: queue decisions for follow-up verification, cooldown override, ignore, or possible monitoring.
  - Phase 5 - Verify: after explicit user approval is recorded with `human-review decide`, run company research, financial checks, filings, news, sentiment, risks, and thesis impact for approved candidates.
  - Phase 6 - Promote: after approval and sufficient verification, add to monitoring, create the company file, and schedule future tracking.
  - Current progress: phases 1, 3, and 4 exist for manual market research; phase 2 is partial through candidate grouping; phase 5 can now create verification manifests from approved candidate-review rows and consolidate provider/specialist verification into `candidate_verification_result.md`; phase 6 now has an approval-gated promotion writer for approved and verified `monitoring_candidate` rows.
- [x] Build portfolio review sub-orchestrator.
  - Description: assesses impact across current holdings, monitoring, and rejected buckets.
  - Current progress: first SDK version registered as `portfolio_review_orchestrator`; it summarizes holdings, monitoring, rejected cooldowns, open/approved human-review items, and candidate verification results without trading, moving stocks, or editing files.
- [x] Build memory and evaluation sub-orchestrator.
  - Description: extracts lessons from traces, run summaries, quality reports, provider failures, and user corrections.
  - Current progress: first SDK version registered as `memory_evaluation_orchestrator`; it reviews run metrics, quality reports, reflection, recurring failures, memory drafts, writer review, and finalization without applying memory writes.
- [x] Build main orchestrator aggregation layer.
  - Description: synthesizes all evidence, chooses updates, creates alerts, incorporates human input queue items, and prepares next actions.
  - Current progress: main orchestrator exists and now receives an aggregation packet covering company, market, portfolio, memory/evaluation, candidate verification, and human-review artifacts. Live prompt/output quality still needs iterative validation.
- [x] Inject operational memory into specialist prompts.
  - Description: orchestrator should call `python -m stock_research memory context --task TASK` or the equivalent Python function and pass the relevant lessons into each specialist prompt before execution.
- [x] Build human review queue.
  - Description: collects moves, strategy changes, and high-impact recommendations for user approval.
  - Current progress: durable queue, digest, and deterministic decision updater are implemented; follow-up actions remain separate approval-gated commands.

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
- [x] Add memory update draft/apply workflow.
  - Description: convert reflection and recurring-failure proposals into schema-valid `memory_update_drafts` artifacts, block invalid/duplicate drafts, and apply approved ready drafts through `memory apply-updates`.
- [x] Add prompt-ready memory context.
  - Description: expose `python -m stock_research memory prompt-context --task TASK` so future orchestrators can inject ranked task-relevant operational memory into specialist prompts.
- [x] Build LLM memory writer agent.
  - Description: bounded specialist that improves/summarizes deterministic draft items. It can run deterministically or through OpenAI Responses API structured output, but it does not write freely; actual memory writes still go through schema validation and `memory apply-updates`.
- [x] Add recurring failure detection.
  - Description: detect repeated provider failures, noisy alerts, missing citations, bad routing, and repeated user corrections across runs.
- [x] Add deterministic run finalization command.
  - Description: write post-run reflection, recurring-failure reports, and finalization artifacts with one command for future scheduler/orchestrator use.
- [x] Wire run finalization into scheduled/orchestrated runs.
  - Description: `run-weekly --write` calls memory finalization after provider tasks, analysis tasks, run summary, and quality report generation.
- [x] Wire bounded memory writer review into scheduled/orchestrated runs.
  - Description: `run-weekly --write` calls bounded memory writer review after finalization and can optionally execute the OpenAI-backed writer.

## Priority 8: Quality, Evaluation, and Automation Hardening

- [ ] Run prompt/output quality iteration on realistic manual and weekly-style examples.
  - Description: inspect actual reports for usefulness, specificity, citation quality, and next-action clarity; improve prompts and schemas until output quality matches expectations.
- [ ] Add golden/failure tests.
  - Description: cover provider failures, malformed specialist output, missing citations, stale approvals, duplicate HRQ decisions, and unsupported review statuses.
- [ ] Strengthen guardrails.
  - Description: enforce no writes outside allowed targets, no Grok-only promotion, no overconfident claims without sources, and no buy/sell/position-size action outside human review.
- [ ] Add specialist/provider depth only where real runs show gaps.
  - Description: prioritize macro providers, European filing coverage, earnings/transcripts, and alert specialists based on quality gaps discovered in live runs.
- [ ] Add model selection optimization.
  - Description: later route cheaper/faster models to low-risk scans and stronger models to high-impact synthesis, holdings, candidate discovery, and complex sentiment.
- [ ] Add scheduling and notification automation.
  - Description: after manual quality is stable, use Codex/app automation or external scheduler for Saturday runs and review notifications.
- [ ] Wire scheduled market-research fanout later.
  - Description: keep market research manual-first until prompts, candidate quality, and review workflow are stable.

## Open Decisions

- Priority European markets: all major European exchanges or start with UK, Germany, France, Netherlands, Nordics, Switzerland?
- Confidence format: numeric score, low/medium/high, or evidence-grade rubric?
- Provider source-of-truth hierarchy when metrics conflict.
- Human approval gates for file writes, stock movement, and strategy changes.
- First test stock universe.
- First stock universe to test beyond the current smoke-test artifacts.
