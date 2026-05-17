# Investment Agent Backlog

Last updated: 2026-05-16

## Purpose

This is the clear task backlog for building the stock tracking and investment research repo. It complements the longer architecture document in `docs/descriptions/investment_agent_workflow.md`.

## Confirmed Decisions

- Scope: US and Europe.
- Outputs: tracked-stock change alerts and new-stock discovery alerts.
- Initial approved providers: Exa, xAI/Grok, SEC, yfinance, FMP, Polygon, Alpha Vantage.
- Automation cadence: the first Codex app automation runs tracked-stock research every two weeks on Saturday at 08:00.
- Review rhythm: user reviews results after the Saturday run, normally on Sunday before planning the week.
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
- [x] Create concise human usage guide.
  - Description: explain in practical language what the user should ask Codex, where results are written, how to review HRQ decisions, and how to start a new chat.
  - Output: `docs/HUMAN_USAGE_GUIDE.md`.
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
- [x] Add initial model routing optimization.
  - Description: `agents/model_routing.yaml` and `stock_research/model_routing.py` now route OpenAI SDK, memory-writer, and xAI/Grok X-search model choices by task complexity and provider need. Current default keeps `grok-4.3` for X.com-native sentiment/discovery, uses `gpt-5.5` for strong OpenAI API synthesis, and uses `gpt-5.4-mini` for balanced/fast lower-complexity synthesis.
- [ ] Tune Grok model routing after more live X-search output.
  - Description: evaluate whether any future faster Grok tier is good enough for low-priority/simple X scans while keeping the strongest Grok X-search model for holdings, user-requested research, candidate discovery, and complex sentiment synthesis.
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
- [x] Build company file updater.
  - Current progress: deterministic approved-proposal writer exists for SDK proposals with `agent-runtime apply-proposal --proposal-id ORP-0001 --write`; SDK writer specialist now drafts proposal-ready updates inside company-research fanout.
  - New UX target: split company-file changes into low-risk factual updates that can be auto-applied with a clear run summary, versus thesis/status/strategy-changing updates that remain approval-gated in the human review digest.
  - 2026-05-15 user feedback: routine source-backed company-file edits should not ask for approval. Build a scoped factual-update writer that applies low-risk updates and writes an FYI summary showing file, section, source, and short change summary. Keep thesis/opinion/status/strategy/trade-impacting edits approval-gated.
  - 2026-05-16 progress: implemented `python -m stock_research company-file apply-factual-updates --run-id RUN_ID --write`, wired it into weekly runs after executed analysis when opportunity-assessment artifacts exist, wrote `agents/runs/{run_id}/company_file_factual_updates.md`, and refreshed AMZN with clean factual rows. Remaining: broaden beyond opportunity assessments if needed and add thesis/status proposal UX tests.
  - 2026-05-16 completion: thesis/status proposal UX tests now verify approval gating and approved generic-section writes; future enhancements are extension work, not a readiness blocker.
- [x] Build category state updater.
  - Description: append source-linked bucket summaries to holdings, monitoring, and rejected state files without overwriting human notes.
  - Current command: `python -m stock_research category-state update --run-id RUN_ID --write`.
  - 2026-05-16 progress: wired into weekly runs and applied to the current AMZN/AAPL repo state.
- [ ] Build CSV updater.
- [x] Build quality reviewer.
  - Description: SDK quality-review specialist is included in company-research fanout for citation/source/approval-gate checks.

## Priority 6: Orchestration

- [x] Build deterministic weekly runner.
  - Description: `python -m stock_research run-weekly` now chains manifest generation, provider tasks, analysis tasks, run summary, quality report, memory finalization, bounded memory-writer review, company-file factual sync, category state updates, final digest, human-review digest, Codex-supervised review pack, optional SDK orchestration, and orchestration report. Live provider/analysis execution cleans generated run artifacts first to avoid stale duplicate packets on reruns.
- [x] Build OpenAI Agents SDK runtime foundation.
  - Description: implement the dedicated SDK runtime backlog with context, registry, guarded tools, structured outputs, tracing, memory injection, and one specialist-as-tool spike.
  - Current progress: first manual runtime slice is implemented and live-smoke-tested with no quality findings after prompt/tool/validator tightening. `run-weekly --write --execute-orchestrator` is implemented as an opt-in scheduled SDK path, with freshness gating when provider/analysis tasks are dry-run. Full fresh `--execute-providers --execute-analysis --execute-orchestrator` validation completed with no findings after adding generated-artifact cleanup. SDK proposals now flow through `agent-runtime queue-proposals --write --queue-review`, approved individual proposals can be applied through `agent-runtime apply-proposal`, repo/memory inspection tools now wrap Python functions directly with task-specific memory injection, guarded provider/analysis SDK tools plan by default while blocking live side effects unless runtime context grants execution, local SDK hooks now record agent/tool/LLM telemetry plus injected/reported memory ids, SDK timeouts/errors now return blocked reviewable artifacts, memory reflection now reads SDK run metrics, code-level fanout infrastructure exists for sub-orchestrators, and scheduled company-research fanout now runs across current-holding and monitoring tickers with financial, company-news, Exa company-search, SEC filing, sentiment, risk/thesis, writer, and quality-review specialist lanes.
  - Output: `stock_research/agent_runtime/`, `docs/descriptions/openai_agents_sdk_orchestration.md`, tests, `python -m stock_research agent-runtime smoke`, and `python -m stock_research agent-runtime run --run-id RUN_ID --execute --write`.
- [x] Build OS/app scheduled execution.
  - Description: run the tracked-stock workflow automatically on Saturday and support manual trigger flows.
  - Current progress: Codex app automation `biweekly-holdings-and-monitoring-research` runs every two weeks on Saturday at 08:00, starting 2026-05-16. It uses GPT-5.5 high in the Codex app and the exact lower-cost Codex-supervised command `C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis`.
  - Codex-supervised handoff: weekly runs write `agents/runs/{run_id}/codex_supervised_review_pack.md/json`; Codex reads the pack, linked final digest/opportunity reports/quality/memory/hygiene/HRQ artifacts, and writes `agents/runs/{run_id}/codex_supervised_review.md`.
  - Sandbox note: `C:\Users\valen\.codex\rules\default.rules` allowlists the exact Codex-supervised command and equivalent PowerShell wrapper; broad Git commands and arbitrary provider execution remain unallowlisted. The old `--execute-orchestrator` command remains only as an explicit benchmark/remote-mode allowance.
- [x] Build open human-review digest.
  - Description: create a concise report/command that summarizes only open `agents/human_review_queue.md` items, grouped by decision type and priority, with each item showing the HRQ id, ticker/company, recommended user action, confidence/verification status, and link to the deeper evidence artifact.
  - Purpose: the user should not need to manually scan the full markdown table to find what needs attention.
  - Current command: `python -m stock_research human-review digest --write`.
  - Current output: `agents/human_review_digest.md`.
  - 2026-05-15 UX fix: digest now deduplicates regenerated candidate rows by category/target so the user does not see the same company twice from old and fresh runs. Company-file update rows are labeled FYI/legacy instead of normal approval requests.
  - 2026-05-17 UX fix: digest rows now load context from linked `candidate_review.md` rows so each open candidate has a reason-to-care, verification state, expected action, and evidence link. Legacy/stale rows with thin context were superseded instead of shown as ticker-only decisions.
- [x] Build deterministic human-review decision updater.
  - Description: record explicit user decisions on HRQ rows without triggering side effects directly.
  - Current command: `python -m stock_research human-review decide --set HRQ-0004=approved --note "Run verification." --write`.
  - Current behavior: updates `agents/human_review_queue.md`, appends a decision note, refreshes `agents/human_review_digest.md`, and leaves follow-up verification, proposal application, stock moves, or monitoring promotion to separate approval-gated commands.
- [ ] Add review notification automation.
  - Description: after scheduled/manual runs, have Codex/app automation summarize new or high-priority open review items and notify the user by app notification and/or email when there are interesting findings or approvals needed.
  - Rule: notifications summarize `agents/human_review_digest.md`; they are not approvals.
  - Future option: evaluate strict Gmail reply ingestion only after digest quality is stable, with duplicate detection, identity checks, and deterministic decision writing.
  - Timing: implement after the manual review digest is reliable and after the scheduled/manual run flow is stable enough to avoid noisy alerts.
- [x] Add run-end review digest summary.
  - Description: every manual/weekly run should finish by refreshing or summarizing `agents/human_review_digest.md`, including new high-priority items and what the human can decide next.
  - Reason: the user should not need to remember to open review files manually.
  - Current progress: weekly `run-weekly --write` refreshes `agents/human_review_digest.md`, includes it in the workflow step output, and adds a next action when open HRQ items need approve/reject/more-research/leave-open decisions. Manual market-research runs, candidate-review runs, and SDK `agent-runtime run --write` now write a run-local `human_review_digest_summary.md`.
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
  - UX clarification: Grok/X-only leads and Exa-only leads are both pre-verification. The category only explains where the lead came from; approved items enter the same deeper verification loop and produce `candidate_verification_result.md`.
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
  - Current progress: AMZN/AAPL weekly-style output was reviewed and tightened for structure, but user review on 2026-05-12 found the content still failed the product goal. Status labels and internal workflow notes are not acceptable output quality. The next iteration must surface actionable X/community narratives, expert/account viewpoints, bullish/bearish arguments, latest developments, verified vs speculative claims, and clear research decisions.
  - 2026-05-12 repair pass: Grok prompts now request deeper account-aware X research; opportunity/final digest synthesis now surfaces X pulse, bull/bear narratives, accounts/posts, hype/noise, investor implications, concrete news developments, and usefulness gates instead of collapsing to status labels. Existing AMZN/AAPL artifacts were regenerated.
  - 2026-05-12 richer report pass: opportunity reports now include an `Investor Insight Report` section with company/industry context, thesis/trend change, expert/community split from X, non-obvious/under-discussed insights, valuation and analyst target snapshot, peer/competition context, decision table, and next research questions. Existing AMZN/AAPL artifacts were regenerated.
  - 2026-05-12 market report pass: manual market-research reports now preserve richer Exa/Grok evidence instead of reducing it to generic status labels. The report includes executive read, industry/theme context, X/community pulse, trend evolution, candidate pipeline, non-obvious/contrarian angles, decision table, and explicit approve/reject/request-more-research choices.
  - Remaining quality target: this is a stronger first investor-report version, not the ceiling. The target is materially stronger than the user's old standalone Grok PDFs by combining Grok/X, Exa, filings, financials, memory, and specialist synthesis.
  - New acceptance bar: final reports must be at least 3x more useful than a quick standalone Grok/X query, because the repo has Grok plus Exa, filings, financial providers, memory, and specialist orchestration.
  - 2026-05-12 fresh live pass: AMZN company research and `AI semiconductor supply chain and advanced packaging` industry research now run through strengthened Grok/X prompts. The market report now includes concrete X pulse, trend evolution, bull/bear narratives, candidate follow-up, Grok investor scorecard, candidate verification table, hype/noise/rumors, and explicit next research questions. Live run exposed and fixed Windows path-length failures from long provider artifact ids and report loss from truncated Grok evidence packets.
  - 2026-05-12 candidate-review grouping pass: broad Grok/X baskets now collapse into thematic review items such as `EMIB/ASE/LEAP basket` and `glass/inspection/etch basket`; regenerated rows for the same run supersede stale open HRQ rows; the market report, candidate review, and human-review digest were regenerated from a fresh live semiconductor run.
  - 2026-05-13 report cleanup pass: after user review of the semiconductor market report, candidate review, HRQ digest, AMZN opportunity assessment, and weekly final digest, the human-facing formatters were tightened. Visible truncation markers are removed, duplicate report sections were eliminated, internal workflow/status prose moved to audit/context, source ids in market reports became clickable, candidate review now explains its purpose, and HRQ digest rows explain what each approval type means.
  - 2026-05-13 second report-quality pass: after a follow-up review, market reports now avoid letting stale background items dominate the bottom line, remove inline Grok `[[1]]` citation markers from prose, extract more X/community pulse sections, clarify the difference between Grok/X raw scorecards and normalized candidate pipelines, and render human decisions as a table. HRQ digest rows now remove source-id walls and link evidence directly. AMZN opportunity/weekly reports now promote source-backed strategic AI ecosystem signals such as Anthropic, Claude, Bedrock, Trainium, OpenAI, NVIDIA, and Cerebras into tailwinds and non-obvious angles.
  - 2026-05-14 root-cause quality pass: fixes were generalized rather than hand-patched for AMZN/Amkor. Exa company evidence now includes entity descriptions/tickers; Exa source ids are unique per artifact; stale prior-year quarter/results/outlook snippets are blocked from top synthesis; repeated company-profile snippets are filtered from industry context; Grok candidate heading noise is cleaned at extraction time; company-news and financial specialist proposals cite real provider ids or ticker-specific artifact ids; report text repair catches mojibake/truncation markers. Fresh AI-semiconductor and AMZN outputs were regenerated for review.
  - Remaining report-quality gap: keep iterating from real outputs. The core manual market loop is now usable, but candidate follow-up should rank the strongest names inside an approved basket before running expensive verification across every ticker. Add golden tests for no generic placeholder source ids, no stale prior-year top-story evidence, and safe incremental report reruns.
  - 2026-05-16 biweekly run stabilization: metadata-only financial conflicts are now separated from thesis-relevant conflicts. Company-name/share-class differences and exchange aliases no longer keep the scheduled workflow in `needs_review`; KRKNF remains partial because OTC/single-provider coverage is a real limitation. FMP partial endpoint success is preserved when profile data is available but quote/TTM endpoints are blocked by plan coverage. Open HRQ rows no longer make the scheduled run or review pack fail.
  - Remaining report-quality gap: peer/competition extraction and some provider excerpt summaries are still noisy for smaller names. Improve smaller/OTC-name synthesis and add better forward valuation/analyst-target coverage where provider data is sparse.
  - 2026-05-17 user-follow-up research surfaced a concrete small-cap data-quality issue: AXTI's prior opportunity report contained suspicious price/market-cap/P/E values. Implemented cross-provider valuation sanity checks in `financial_compare`, financial specialist review, opportunity reports, and company-file factual updates so small-cap/OTC valuation fields are downgraded and explicitly marked verification-needed when coverage is weak or suspicious.
- [ ] Add golden/failure tests.
  - Description: cover provider failures, malformed specialist output, missing citations, stale approvals, duplicate HRQ decisions, and unsupported review statuses.
  - Current progress: weekly digest and opportunity assessment golden tests cover evidence links, missing evidence, Grok/X social-signal labeling, direct trade language, readable financial formatting, taxonomy-only conflict handling, and missing provider/source ids.
  - 2026-05-12 progress: added investor-usefulness regression coverage for status-only Grok/X output, richer opportunity-report section coverage, and manual market-research report sections/decision wording.
  - 2026-05-13 progress: targeted report-quality tests pass after removing visible truncation and duplicate human-facing sections from generated reports.
  - 2026-05-16 progress: added golden human-facing markdown quality checks for visible truncation, dead numeric citations, unlinked source ids, raw dict/JSON-like dumps, duplicate sections, and status-only Grok/X sentiment; added archive, category-state, run-end digest, and thesis/status proposal UX tests.
  - 2026-05-16 progress: added regression tests for FMP partial endpoint preservation, financial text normalization for share-class/exchange aliases, nonblocking metadata financial reviews, Codex review-pack status with open HRQ rows, and scheduled-run status semantics when human-review rows are open but quality findings are clear.
  - Gap: keep extending fixture cases with stronger examples modeled on the user-provided Grok PDFs, especially fresh live Grok/X industry discovery and company sentiment runs. Add more regression coverage that full raw Grok artifacts feed reports when evidence packet claims are truncated and broad Grok baskets stay concise and thematically named.
- [ ] Strengthen guardrails.
  - Description: enforce no writes outside allowed targets, no Grok-only promotion, no overconfident claims without sources, and no buy/sell/position-size action outside human review.
  - Current progress: final digest and opportunity assessment validators now enforce evidence/source presence, social-signal labeling, direct trade-language blocking, and taxonomy-only conflict handling.
  - Current progress: Grok-only and rumor-like market leads stay verification-limited; candidate-review promotion remains approval-gated.
  - Gap: guardrails must also flag non-actionable synthesis, e.g. `Grok/X social signal: mixed_social_signal` without a narrative summary, no bullish/bearish claim extraction, and watch items that describe internal workflow chores instead of user-facing research decisions.
- [ ] Add specialist/provider depth only where real runs show gaps.
  - Description: prioritize macro providers, European filing coverage, earnings/transcripts, and alert specialists based on quality gaps discovered in live runs.
- [ ] Add model selection optimization.
  - Description: later route cheaper/faster models to low-risk scans and stronger models to high-impact synthesis, holdings, candidate discovery, and complex sentiment.
- [ ] Add scheduling and notification automation.
  - Description: scheduling is implemented through Codex app automation for biweekly tracked-stock runs; notification delivery is still pending.
  - Current progress: `biweekly-holdings-and-monitoring-research` is active in the Codex app, with sandbox rules validated for the exact workflow command.
  - Remaining: add Codex/app notification and/or email digest that summarizes `agents/human_review_digest.md` after runs. Notifications are not approvals.
- [ ] Wire scheduled market-research fanout later.
  - Description: keep market research manual-first until prompts, candidate quality, and review workflow are stable.
- [x] Add artifact lifecycle and archive hygiene.
  - Description: prevent `agents/runs/`, company reports, and candidate artifacts from becoming an unbounded active working set.
  - Current progress: `docs/descriptions/artifact_lifecycle_and_hygiene.md` defines the archive/index approach. `python -m stock_research artifact-hygiene inventory --write` writes `archive/research_index.md`; `python -m stock_research artifact-hygiene archive [--write]` dry-runs or moves only archive-eligible markdown reports into `archive/runs/`; run finalization writes `archive_proposals.md`.
  - Guardrails: never archive active holding/monitoring company files, never delete evidence by default, never archive unresolved HRQ context, and keep rejected cooldown/reason discoverable.

## Open Decisions

- Priority European markets: all major European exchanges or start with UK, Germany, France, Netherlands, Nordics, Switzerland?
- Confidence format: numeric score, low/medium/high, or evidence-grade rubric?
- Provider source-of-truth hierarchy when metrics conflict.
- Human approval gates for file writes, stock movement, and strategy changes.
- First test stock universe.
- First stock universe to test beyond the current smoke-test artifacts.
