# MEMORY.md

Long-term project memory for durable facts and decisions.
Use this file for information we should not lose across sessions.

## Scope and usage

- Keep this file concise and high-signal.
- Store only stable, high-impact decisions/facts.
- Every memory item should include:
  - date,
  - decision/fact,
  - evidence artifact path(s),
  - current status (`active` or `superseded`).
- If a memory changes, update it in place and note what changed.

## Active memory

- 2026-04-30:
  - decision/fact: Initial stock research scope is US and Europe.
  - evidence artifact path(s): `docs/descriptions/investment_agent_workflow.md`, `docs/plans/investment_agent_backlog.md`
  - status: active

- 2026-04-30:
  - decision/fact: The system should produce both tracked-stock change alerts and new-stock discovery alerts when candidates match the strategy.
  - evidence artifact path(s): `docs/descriptions/investment_agent_workflow.md`, `docs/plans/investment_agent_backlog.md`
  - status: active

- 2026-04-30:
  - decision/fact: Approved initial data providers are Exa, xAI/Grok, SEC, yfinance, FMP, Polygon, and Alpha Vantage. Additional candidates may be evaluated before implementation.
  - evidence artifact path(s): `docs/descriptions/investment_agent_workflow.md`, `docs/plans/investment_agent_backlog.md`
  - status: active

- 2026-04-30:
  - decision/fact: Full recurring research should run weekly on Saturday so Sunday can be used for review and planning.
  - evidence artifact path(s): `docs/descriptions/investment_agent_workflow.md`, `docs/plans/investment_agent_backlog.md`
  - status: active

- 2026-04-30:
  - decision/fact: Rejected stocks should have a 6-week cooldown before they can surface again as promising candidates.
  - evidence artifact path(s): `docs/descriptions/investment_agent_workflow.md`, `docs/plans/investment_agent_backlog.md`
  - status: active

- 2026-04-30:
  - decision/fact: Stock tracking file conventions are established with category CSVs/state files, company markdown template, strategy starter files, and market research folder conventions.
  - evidence artifact path(s): `stock_tracking/current_holdings/current_holdings.csv`, `stock_tracking/current_holdings/current_holdings_state.md`, `stock_tracking/monitoring/monitoring.csv`, `stock_tracking/monitoring/monitoring_state.md`, `stock_tracking/rejected/rejected.csv`, `stock_tracking/rejected/rejected_state.md`, `docs/templates/company_stock_info_template.md`, `docs/templates/stock_tracking_csv_schema.md`, `strategy/investment_strategy.md`, `market_research/README.md`
  - status: active

- 2026-05-03:
  - decision/fact: Codex chat is the primary human interface. User ideas should be captured through a human input queue and translated into durable repo state so the automated workflow can pick them up. This is separate from the human review queue for system-generated approval items.
  - evidence artifact path(s): `docs/descriptions/human_interaction_workflow.md`, `docs/descriptions/repo_map.md`, `docs/plans/human_research_requests.md`, `strategy/research_priorities.md`, `agents/human_review_queue.md`
  - status: active

- 2026-05-03:
  - decision/fact: The repo is published to GitHub at `https://github.com/muhuuh/picker` with `main` as the tracked branch. Local `.env` files are ignored and should not be committed.
  - evidence artifact path(s): `.gitignore`, `docs/scratchpads/github_publish_scratchpad.md`
  - status: active

- 2026-05-03:
  - decision/fact: A stdlib-only Python deterministic core now exists under `stock_research/`. It can summarize repo state, validate CSV schemas, load human requests/research priorities/review queue, classify and queue human requests, scan stale rows, summarize rejected cooldowns, and generate weekly manifests.
  - evidence artifact path(s): `stock_research/`, `README.md`, `SETUP.md`, `tests/`
  - status: active

- 2026-05-03:
  - decision/fact: Human request routing is implemented in `stock_research.router`. The CLI can now append and route requests into durable artifacts with `python -m stock_research route-request "..."`.
  - evidence artifact path(s): `stock_research/router.py`, `stock_research/cli.py`, `tests/test_request_router.py`, `README.md`, `SETUP.md`
  - status: active

- 2026-05-03:
  - decision/fact: Provider-neutral source and evidence packet schemas are implemented in `stock_research.evidence`. Future provider tools should output this schema and store packets under `agents/runs/{run_id}/evidence_packets/`.
  - evidence artifact path(s): `stock_research/evidence.py`, `docs/descriptions/evidence_schema.md`, `tests/test_evidence.py`, `README.md`, `SETUP.md`
  - status: active

- 2026-05-03:
  - decision/fact: SEC EDGAR is the first provider integration. It uses official SEC JSON APIs, needs no API key, and requires a declared `User-Agent` via `SEC_USER_AGENT`, `STOCK_RESEARCH_SEC_USER_AGENT`, or `--user-agent`.
  - evidence artifact path(s): `stock_research/providers/sec_edgar.py`, `docs/descriptions/sec_edgar_provider.md`, `.env.example`, `tests/test_sec_edgar_provider.py`
  - status: active

- 2026-05-03:
  - decision/fact: SEC EDGAR live smoke test passed for AAPL after adding compressed-response handling. The run wrote raw submissions JSON and a provider-neutral evidence packet.
  - evidence artifact path(s): `agents/runs/2026-05-09_weekly/raw/sec_edgar/AAPL_submissions.json`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_sec_edgar_company_aapl.json`, `stock_research/providers/sec_edgar.py`, `tests/test_sec_edgar_provider.py`
  - status: active

- 2026-05-03:
  - decision/fact: yfinance and Exa provider tools are implemented. yfinance live smoke test passed for AAPL. Exa search and contents live smoke tests passed after adding explicit `User-Agent` and `Accept` headers.
  - evidence artifact path(s): `stock_research/providers/yfinance_provider.py`, `stock_research/providers/exa.py`, `docs/descriptions/yfinance_provider.md`, `docs/descriptions/exa_provider.md`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_yfinance_company_aapl.json`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_exa_industry_semiconductors.json`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_exa_theme_sec_edgar_docs.json`
  - status: active

- 2026-05-03:
  - decision/fact: Exa should be used both as a default deterministic weekly kickoff gatherer and as a callable provider tool for later specialist agents. Weekly kickoff should use Exa news for current holdings and monitoring stocks, industry/general/company search for research priorities and human input queue items, and contents extraction for high-value result follow-up.
  - evidence artifact path(s): `docs/descriptions/exa_provider.md`, `docs/descriptions/investment_agent_workflow.md`, `docs/plans/investment_agent_backlog.md`, `docs/scratchpads/agent_orchestration_scratchpad.md`
  - status: active

- 2026-05-03:
  - decision/fact: Weekly manifests now include deterministic `provider_tasks` for SEC, yfinance, and Exa. A dry-run-by-default provider task runner can inspect or explicitly execute those tasks with `python -m stock_research provider-tasks --manifest PATH [--execute]`.
  - evidence artifact path(s): `stock_research/manifest.py`, `stock_research/provider_runner.py`, `stock_research/cli.py`, `tests/test_stock_research_core.py`, `tests/test_provider_runner.py`, `agents/runs/2026-05-09_weekly/manifest.json`
  - status: active

- 2026-05-04:
  - decision/fact: A dry-run-by-default analysis task runner is implemented. Use `python -m stock_research analysis-tasks --manifest PATH [--execute]` to execute deterministic post-provider analysis tasks such as `financial_compare` and `financial_review` in dependency order.
  - evidence artifact path(s): `stock_research/analysis_runner.py`, `stock_research/cli.py`, `tests/test_analysis_runner.py`, `docs/descriptions/analysis_task_runner.md`
  - status: active

- 2026-05-04:
  - decision/fact: Deterministic run summary and quality report generators are implemented. Use `python -m stock_research run-summary --run-id RUN_ID --write` and `python -m stock_research quality-report --run-id RUN_ID --write` before memory finalization.
  - evidence artifact path(s): `stock_research/run_summary.py`, `stock_research/quality_report.py`, `tests/test_run_summary.py`, `tests/test_quality_report.py`, `docs/descriptions/run_summary_and_quality.md`, `agents/runs/2026-05-09_weekly/run_summary.md`, `agents/runs/2026-05-09_weekly/quality_report.md`
  - status: active

- 2026-05-03:
  - decision/fact: Direct X.com API recent search/counts was the wrong implementation path and is superseded. The repo should use xAI/Grok with built-in `x_search` via `XAI_API_KEY` for X sentiment/latest-news research.
  - evidence artifact path(s): `stock_research/providers/xai_grok.py`, `docs/descriptions/xai_grok_provider.md`, `tests/test_xai_grok_provider.py`, `stock_research/manifest.py`, `stock_research/provider_runner.py`
  - status: active

- 2026-05-03:
  - decision/fact: xAI/Grok `x_search` should be used in two places: as a deterministic weekly kickoff provider task and as a callable tool for future xAI Grok stock/industry sentiment specialists. Its output is social sentiment/narrative discovery; material factual claims should be verified with Exa, SEC, yfinance, FMP, Polygon, Alpha Vantage, or other primary/market-data sources before updating investment conclusions.
  - evidence artifact path(s): `docs/descriptions/investment_agent_workflow.md`, `docs/descriptions/xai_grok_provider.md`, `docs/plans/investment_agent_backlog.md`, `docs/scratchpads/agent_orchestration_scratchpad.md`
  - status: active

- 2026-05-03:
  - decision/fact: xAI/Grok live `x_search` smoke test passed for AMD with a 2026-05-01 to 2026-05-03 window. The tool wrote raw Grok output and a validated provider-neutral evidence packet.
  - evidence artifact path(s): `agents/runs/2026-05-09_weekly/raw/xai_grok/x_search_amd.json`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_xai_grok_company_amd.json`
  - status: active

- 2026-05-03:
  - decision/fact: FMP, Polygon/Massive, and Alpha Vantage provider tools are implemented as market-data cross-check integrations and are wired into CLI, provider-task execution, and weekly manifests. Live AAPL smoke tests passed on 2026-05-04 after adding Alpha Vantage request throttling for free-tier limits.
  - evidence artifact path(s): `stock_research/providers/fmp.py`, `stock_research/providers/polygon_provider.py`, `stock_research/providers/alpha_vantage.py`, `docs/descriptions/fmp_provider.md`, `docs/descriptions/polygon_provider.md`, `docs/descriptions/alpha_vantage_provider.md`, `tests/test_fmp_provider.py`, `tests/test_polygon_provider.py`, `tests/test_alpha_vantage_provider.py`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_fmp_company_aapl.json`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_polygon_company_aapl.json`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_alpha_vantage_company_aapl.json`
  - status: active

- 2026-05-04:
  - decision/fact: Financial provider reconciliation should be deterministic before LLM synthesis. `financial_compare` compares yfinance/FMP/Polygon/Massive/Alpha/SEC financial packets, excludes Exa/Grok by design, preserves material provider conflicts, and writes a provider-neutral evidence packet for later financial-data specialists.
  - evidence artifact path(s): `stock_research/financial_compare.py`, `docs/descriptions/financial_compare.md`, `tests/test_financial_compare.py`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_financial_compare_company_aapl.json`
  - status: active

- 2026-05-04:
  - decision/fact: The first deterministic financial-data specialist is implemented. Use `python -m stock_research financial review --ticker TICKER --run-id RUN_ID` after `financial_compare`; it writes a specialist evidence packet, raw review JSON, and markdown review, and marks whether company-file financial updates are ready, partial, or need human review.
  - evidence artifact path(s): `stock_research/financial_specialist.py`, `docs/descriptions/financial_data_specialist.md`, `tests/test_financial_specialist.py`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_financial_data_specialist_company_aapl.json`, `agents/runs/2026-05-09_weekly/reports/financial_data_specialist/AAPL_financial_review.md`
  - status: active

- 2026-05-04:
  - decision/fact: Operational agent memory is implemented under `agents/memory/` as structured Markdown plus deterministic Python inspection commands. It stores orchestration lessons, source-quality notes, specialist playbooks, evaluation metrics, and deprecated operational behavior. It must not store secrets, raw provider output, or ordinary company investment facts.
  - evidence artifact path(s): `agents/memory/README.md`, `agents/memory/memory_index.md`, `stock_research/memory.py`, `docs/descriptions/agent_memory_workflow.md`, `docs/templates/agent_memory_item_template.md`
  - status: active

- 2026-05-04:
  - decision/fact: The operational memory layer is not yet fully autonomous. Scheduled deterministic run finalization and bounded memory-writer review are now wired into `run-weekly --write`; pending learning-loop work is automatic task-relevant memory injection into actual LLM specialist prompts after the agent framework is chosen.
  - evidence artifact path(s): `stock_research/scheduled_runner.py`, `docs/plans/investment_agent_backlog.md`, `docs/plans/investment_agent_workflow_plan.md`, `agents/memory/evaluation_metrics.md`, `docs/descriptions/agent_memory_workflow.md`, `docs/descriptions/llm_memory_writer.md`, `docs/descriptions/scheduled_runner.md`
  - status: active

- 2026-05-04:
  - decision/fact: Deterministic operational memory writer/update commands are implemented. Use `python -m stock_research memory add ...` for schema-valid additions and `python -m stock_research memory deprecate --id ITEM_ID --reason "..."` for deprecations.
  - evidence artifact path(s): `stock_research/memory.py`, `stock_research/cli.py`, `tests/test_memory.py`, `agents/memory/evaluation_metrics.md`
  - status: active

- 2026-05-04:
  - decision/fact: Deterministic post-run memory reflection and memory update proposal generation are implemented. Use `python -m stock_research memory reflect-run --run-id RUN_ID --write` to create `memory_reflection.json` and `memory_reflection.md`; proposals are not applied automatically.
  - evidence artifact path(s): `stock_research/memory_reflection.py`, `stock_research/cli.py`, `tests/test_memory_reflection.py`, `agents/runs/2026-05-09_weekly/memory_reflection.md`
  - status: active

- 2026-05-04:
  - decision/fact: Deterministic recurring failure detection is implemented. Use `python -m stock_research memory recurring-failures --write` to scan reflected runs and write recurring failure reports under `agents/memory/`.
  - evidence artifact path(s): `stock_research/memory_reflection.py`, `stock_research/cli.py`, `tests/test_memory_reflection.py`, `agents/memory/recurring_failures.md`
  - status: active

- 2026-05-04:
  - decision/fact: Deterministic run finalization is implemented. Use `python -m stock_research memory finalize-run --run-id RUN_ID` to write post-run reflection, recurring-failure, and finalization artifacts. Actual scheduled/orchestrator invocation is still pending.
  - evidence artifact path(s): `stock_research/run_finalization.py`, `stock_research/cli.py`, `tests/test_memory_reflection.py`, `agents/runs/2026-05-09_weekly/finalization.md`
  - status: active

- 2026-05-05:
  - decision/fact: The learning-loop memory workflow is the current priority over adding another provider/specialist. Memory update proposals can now be converted into schema-valid drafts with `python -m stock_research memory draft-updates --run-id RUN_ID --write`, applied after approval with `memory apply-updates`, and formatted for future specialist prompt injection with `memory prompt-context --task TASK`.
  - evidence artifact path(s): `stock_research/memory_updates.py`, `stock_research/memory.py`, `stock_research/cli.py`, `docs/descriptions/agent_memory_workflow.md`, `docs/plans/investment_agent_backlog.md`
  - status: active

- 2026-05-05:
  - decision/fact: Bounded LLM memory writer review is implemented. It builds review prompts, can run deterministic review or optional OpenAI Responses API structured output with `OPENAI_API_KEY`, writes review artifacts only when requested, can update draft artifacts, and still cannot directly edit `agents/memory/*.md`; approved writes must go through deterministic `memory apply-updates`.
  - evidence artifact path(s): `stock_research/memory_llm_writer.py`, `tests/test_memory_llm_writer.py`, `docs/descriptions/llm_memory_writer.md`, `agents/runs/2026-05-09_weekly/memory_writer_review.md`
  - status: active

- 2026-05-05:
  - decision/fact: Deterministic weekly orchestration is implemented through `python -m stock_research run-weekly`. It chains manifest generation, provider task dry-run/execute, analysis task dry-run/execute, run summary, quality report, memory finalization, bounded memory-writer review, and orchestration report, then stops at the agent-framework decision boundary.
  - evidence artifact path(s): `stock_research/scheduled_runner.py`, `tests/test_scheduled_runner.py`, `docs/descriptions/scheduled_runner.md`, `README.md`, `SETUP.md`
  - status: active

- 2026-05-06:
  - decision/fact: OpenAI Agents SDK is selected as the agent orchestration framework. The first runtime foundation is implemented with `stock_research/agent_runtime/`, central registry, main orchestrator builder, company-news specialist builder, specialist-as-tool composition, typed context/output contracts, prompt/spec files, trace/run config helpers, tests, a no-model-call smoke CLI, a live manual `agent-runtime run --execute --write` command, and opt-in scheduled orchestration through `run-weekly --write --execute-orchestrator`. Scheduled SDK runs mark actionable output from dry-run provider/analysis inputs as `needs_review`.
  - evidence artifact path(s): `stock_research/agent_runtime/`, `agents/orchestrator/prompts/main.md`, `agents/orchestrator/specs/main.md`, `agents/specialists/prompts/company_news.md`, `agents/specialists/specs/company_news.md`, `tests/test_agent_runtime.py`, `agents/runs/2026-05-09_weekly/agent_runtime_main_orchestrator.md`, `agents/runs/2026-05-09_weekly/run_metrics.md`, `agents/runs/2026-05-09_weekly/trace_links.md`, `docs/scratchpads/openai_agents_sdk_orchestration_scratchpad.md`, `docs/plans/openai_agents_sdk_orchestration_backlog.md`
  - status: active

- 2026-05-06:
  - decision/fact: Fresh scheduled provider/analysis execution cleans generated artifacts in the target run directory before rebuilding evidence, reports, and SDK outputs. This prevents repeated smoke tests or reruns for the same run id from double-counting stale evidence packets.
  - evidence artifact path(s): `stock_research/scheduled_runner.py`, `tests/test_scheduled_runner.py`, `docs/descriptions/scheduled_runner.md`, `agents/runs/2026-05-09_weekly/run_summary.md`, `agents/runs/2026-05-09_weekly/orchestration_report.md`
  - status: active

- 2026-05-07:
  - decision/fact: SDK file update proposals now have a deterministic review bridge. Use `python -m stock_research agent-runtime queue-proposals --run-id RUN_ID --write --queue-review` to write `orchestrator_update_proposals.md` and duplicate-safe human-review queue rows. This bridge does not edit company files.
  - evidence artifact path(s): `stock_research/agent_runtime/proposal_review.py`, `tests/test_agent_runtime_proposal_review.py`, `agents/runs/2026-05-09_weekly/orchestrator_update_proposals.md`, `agents/human_review_queue.md`, `docs/descriptions/openai_agents_sdk_orchestration.md`
  - status: active

- 2026-05-07:
  - decision/fact: Approved SDK file update proposals can now be applied through a deterministic writer. Use `python -m stock_research agent-runtime apply-proposal --run-id RUN_ID --proposal-id ORP-0001 --write`; it refuses missing/open/rejected review rows, validates the target is under `stock_tracking/stock_info_files/`, updates source/change logs, and writes an application report.
  - evidence artifact path(s): `stock_research/agent_runtime/proposal_writer.py`, `tests/test_agent_runtime_proposal_writer.py`, `docs/descriptions/openai_agents_sdk_orchestration.md`
  - status: active

- 2026-05-07:
  - decision/fact: SDK repo/memory inspection is now function-first and task-memory aware. Runtime contexts separate task-relevant `memory_item_ids` from validator-only `known_memory_item_ids`, company-news specialist-as-tool receives company-news memory, and SDK repo tools can load repo map, run summary, quality report, memory prompt context, and evidence packet indexes without CLI subprocesses.
  - evidence artifact path(s): `stock_research/agent_runtime/context.py`, `stock_research/agent_runtime/tools/repo_tools.py`, `stock_research/agent_runtime/orchestrators/main.py`, `tests/test_agent_runtime.py`, `docs/descriptions/openai_agents_sdk_orchestration.md`
  - status: active

- 2026-05-07:
  - decision/fact: SDK provider and analysis tools are function-first and guarded. `run_provider_tasks_guarded` and `run_analysis_tasks_guarded` wrap manifest runner functions directly, plan by default, and block live side effects unless the runtime context has `dry_run=False` and the matching execute permission.
  - evidence artifact path(s): `stock_research/agent_runtime/tools/provider_tools.py`, `stock_research/agent_runtime/tools/analysis_tools.py`, `stock_research/agent_runtime/orchestrators/main.py`, `tests/test_agent_runtime.py`, `docs/descriptions/openai_agents_sdk_orchestration.md`
  - status: active

- 2026-05-10:
  - decision/fact: SDK runtime local telemetry hooks are implemented. `run_metrics.md` records agent lifecycle, tool calls, LLM calls/usage when available, injected operational memory ids, and final-output reported memory ids without logging raw prompts/tool payloads.
  - evidence artifact path(s): `stock_research/agent_runtime/tracing.py`, `stock_research/agent_runtime/runner.py`, `tests/test_agent_runtime.py`, `docs/descriptions/openai_agents_sdk_orchestration.md`
  - status: active

- 2026-05-10:
  - decision/fact: SDK timeout/error policy and telemetry-informed memory reflection are implemented. Live SDK timeouts/errors now produce blocked reviewable runtime artifacts and `run_metrics.md`; post-run reflection reads those metrics and surfaces SDK failures or missing metrics as learning-loop issues.
  - evidence artifact path(s): `stock_research/agent_runtime/runner.py`, `stock_research/memory_reflection.py`, `stock_research/scheduled_runner.py`, `stock_research/cli.py`, `tests/test_agent_runtime.py`, `tests/test_memory_reflection.py`, `docs/plans/openai_agents_sdk_orchestration_backlog.md`
  - status: active

- 2026-05-10:
  - decision/fact: Code-level SDK fanout infrastructure is implemented. `stock_research/agent_runtime/fanout.py` can run independent agent tasks concurrently with task-specific memory, per-task timeout, partial-failure preservation, and aggregate metrics; scheduled sub-orchestrator integration is still pending.
  - evidence artifact path(s): `stock_research/agent_runtime/fanout.py`, `tests/test_agent_runtime.py`, `docs/plans/openai_agents_sdk_orchestration_backlog.md`, `docs/scratchpads/openai_agents_sdk_orchestration_scratchpad.md`
  - status: active

- 2026-05-10:
  - decision/fact: The first company-research SDK sub-orchestrator is implemented. `company_research_orchestrator` is registered, exposed to the main orchestrator, can build one-ticker company research packets across financials/company-news/filings/sentiment/company-search/risk-thesis lanes, and can aggregate available fanout results while preserving missing lanes as next-run tasks.
  - evidence artifact path(s): `stock_research/agent_runtime/orchestrators/company_research.py`, `agents/orchestrator/prompts/company_research.md`, `agents/orchestrator/specs/company_research.md`, `stock_research/agent_runtime/registry.py`, `stock_research/agent_runtime/orchestrators/main.py`, `tests/test_agent_runtime.py`, `docs/plans/openai_agents_sdk_orchestration_backlog.md`
  - status: active

- 2026-05-10:
  - decision/fact: The first SDK financial specialist is implemented. `financial_specialist` is registered, exposed to the main and company-research orchestrators, and runs in company-research fanout alongside company-news synthesis while preserving deterministic `financial_compare` and financial review artifacts as the required source of financial truth.
  - evidence artifact path(s): `stock_research/agent_runtime/specialists/financial.py`, `agents/specialists/prompts/financial.md`, `agents/specialists/specs/financial.md`, `stock_research/agent_runtime/orchestrators/company_research.py`, `stock_research/agent_runtime/orchestrators/main.py`, `tests/test_agent_runtime.py`
  - status: active

- 2026-05-10:
  - decision/fact: The first SDK xAI/Grok sentiment specialist is implemented. `sentiment_specialist` is registered, exposed to the main and company-research orchestrators, and runs in company-research fanout using existing xAI/Grok `x_search` artifacts as social-signal evidence only. Sentiment memory selection now includes the active direct-X replacement rule.
  - evidence artifact path(s): `stock_research/agent_runtime/specialists/sentiment.py`, `agents/specialists/prompts/sentiment.md`, `agents/specialists/specs/sentiment.md`, `stock_research/memory.py`, `stock_research/agent_runtime/orchestrators/company_research.py`, `stock_research/agent_runtime/orchestrators/main.py`, `tests/test_agent_runtime.py`
  - status: active

- 2026-05-10:
  - decision/fact: The first SDK SEC filing specialist is implemented. `filing_specialist` is registered, exposed to the main and company-research orchestrators, and runs in company-research fanout using existing SEC EDGAR artifacts as filing evidence.
  - evidence artifact path(s): `stock_research/agent_runtime/specialists/filing.py`, `agents/specialists/prompts/filing.md`, `agents/specialists/specs/filing.md`, `stock_research/agent_runtime/orchestrators/company_research.py`, `stock_research/agent_runtime/orchestrators/main.py`, `tests/test_agent_runtime.py`
  - status: active

- 2026-05-10:
  - decision/fact: The SDK Exa company-search specialist and deterministic Exa company-search provider planning are implemented generically for tracked tickers and human stock-research tickers. Company-research fanout task ids include the ticker only as a per-run task label, not as ticker-specific agent code.
  - evidence artifact path(s): `stock_research/agent_runtime/specialists/company_search.py`, `agents/specialists/prompts/company_search.md`, `agents/specialists/specs/company_search.md`, `stock_research/manifest.py`, `stock_research/agent_runtime/orchestrators/company_research.py`, `stock_research/agent_runtime/orchestrators/main.py`, `tests/test_agent_runtime.py`, `tests/test_stock_research_core.py`
  - status: active

- 2026-05-10:
  - decision/fact: Scheduled SDK company research fanout is implemented for all current-holding and monitoring tickers. `run-weekly --write --execute-orchestrator` now runs generic per-ticker company-research packets before main orchestration, including financial, company-news, Exa company-search, SEC filing, xAI/Grok sentiment, risk/thesis, writer, and quality-review lanes, and writes per-ticker company-research markdown/metrics artifacts.
  - evidence artifact path(s): `stock_research/scheduled_runner.py`, `stock_research/agent_runtime/orchestrators/company_research.py`, `stock_research/agent_runtime/specialists/risk_thesis.py`, `stock_research/agent_runtime/specialists/writer.py`, `stock_research/agent_runtime/specialists/quality_review.py`, `stock_research/agent_runtime/reports.py`, `tests/test_scheduled_runner.py`, `tests/test_agent_runtime.py`
  - status: active

- 2026-05-10:
  - decision/fact: Market discovery must use xAI/Grok `x_search` as a first-class lane for X-based niche trends, hype, rumors, community sentiment, and emerging ticker leads, alongside Exa/web discovery for verification. Grok/X output remains social signal and lead generation only; material claims and candidate promotion require Exa, filings, or market-data verification.
  - evidence artifact path(s): `stock_research/agent_runtime/orchestrators/market_research.py`, `stock_research/agent_runtime/specialists/grok_discovery.py`, `stock_research/agent_runtime/specialists/exa_industry.py`, `stock_research/agent_runtime/specialists/discovery.py`, `stock_research/providers/xai_grok.py`, `stock_research/manifest.py`, `docs/descriptions/xai_grok_provider.md`, `tests/test_agent_runtime.py`, `tests/test_stock_research_core.py`
  - status: active

- 2026-05-10:
  - decision/fact: The near-term discovery workflow should be manual-first, not scheduled-first. `python -m stock_research market-research run --topic TOPIC --subject-type industry|theme --write [--execute-providers] [--execute-orchestrator]` is the clean manual loop for industry/theme research. It plans Exa context, Exa company discovery, and Grok/X discovery, writes a market report, extracts typed candidate leads, and applies discovery gates for Grok-only leads, rejected cooldowns, source ids, and verification labels.
  - evidence artifact path(s): `stock_research/market_research_runner.py`, `stock_research/cli.py`, `stock_research/agent_runtime/outputs.py`, `tests/test_market_research_runner.py`, `README.md`, `SETUP.md`
  - status: active

- 2026-05-10:
  - decision/fact: Manual market-research candidate leads now flow through a deterministic human-review bridge. `python -m stock_research market-research candidate-review --run-id RUN_ID --write --queue-review` groups duplicate/share-class leads, writes `candidate_review.md`, and appends duplicate-safe review rows for verification or possible monitoring decisions. It does not add stocks to monitoring.
  - evidence artifact path(s): `stock_research/candidate_review.py`, `stock_research/cli.py`, `tests/test_market_research_runner.py`, `agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_review.md`, `agents/human_review_queue.md`
  - status: active

- 2026-05-11:
  - decision/fact: Approved candidate-review rows can now be converted into verification manifests. `python -m stock_research market-research candidate-followup --run-id RUN_ID --review-id HRQ-0004 --write` writes provider/analysis verification tasks for existing runners and does not add stocks to monitoring.
  - evidence artifact path(s): `stock_research/candidate_followup.py`, `stock_research/cli.py`, `tests/test_market_research_runner.py`, `docs/plans/openai_agents_sdk_orchestration_backlog.md`
  - status: active

- 2026-05-11:
  - decision/fact: Discovery candidates can only be promoted to monitoring through an approval-gated and verification-gated writer. `python -m stock_research market-research candidate-promote --run-id RUN_ID --review-id HRQ-0004 --write` requires an approved `monitoring_candidate` HRQ row and required verification reports before writing the monitoring CSV row and company file.
  - evidence artifact path(s): `stock_research/candidate_promotion.py`, `stock_research/cli.py`, `tests/test_market_research_runner.py`, `docs/plans/openai_agents_sdk_orchestration_backlog.md`
  - status: active

- 2026-05-11:
  - decision/fact: Open human-review items can now be summarized through a deterministic digest. `python -m stock_research human-review digest --write` writes `agents/human_review_digest.md`, grouping open review items by decision type and priority with suggested user actions.
  - evidence artifact path(s): `stock_research/human_review_digest.py`, `stock_research/cli.py`, `tests/test_human_review_digest.py`, `agents/human_review_digest.md`
  - status: active

- 2026-05-11:
  - decision/fact: Explicit user decisions on human-review queue rows can now be recorded deterministically. `python -m stock_research human-review decide --set HRQ-0004=approved --note "Run verification." --write` updates queue status/notes and refreshes the digest, but does not run follow-up verification, promotion, or file writes by itself.
  - evidence artifact path(s): `stock_research/human_review_decisions.py`, `stock_research/cli.py`, `tests/test_human_review_decisions.py`, `agents/human_review_queue.md`, `agents/human_review_digest.md`
  - status: active

- 2026-05-11:
  - decision/fact: Candidate verification now has a consolidated result report. After approved candidate follow-up provider/analysis tasks run, use `python -m stock_research market-research candidate-verification-result --run-id RUN_ID --review-id HRQ-0004 --write` to summarize provider coverage, specialist statuses, findings, and next actions before any monitoring promotion.
  - evidence artifact path(s): `stock_research/candidate_verification_result.py`, `tests/test_market_research_runner.py`, `agents/runs/2026-05-10_manual-market-energy-storage/market_research/candidate_verification_result.md`
  - status: active

- 2026-05-11:
  - decision/fact: The first portfolio review sub-orchestrator is implemented. `portfolio_review_orchestrator` is registered in the OpenAI Agents SDK runtime, exposed to the main orchestrator, and can build/write bucket-level review packets from holdings, monitoring, rejected cooldowns, open/approved human-review items, and candidate verification results without trading or editing stock files.
  - evidence artifact path(s): `stock_research/agent_runtime/orchestrators/portfolio_review.py`, `agents/orchestrator/prompts/portfolio_review.md`, `agents/orchestrator/specs/portfolio_review.md`, `tests/test_agent_runtime.py`, `agents/runs/2026-05-10_manual-market-energy-storage/portfolio_review/portfolio_review.md`
  - status: active

- 2026-05-11:
  - decision/fact: The first memory/evaluation sub-orchestrator is implemented. `memory_evaluation_orchestrator` is registered in the OpenAI Agents SDK runtime, exposed to the main orchestrator, and can build/write learning-loop review packets from run telemetry, quality reports, memory reflection, recurring failures, memory update drafts, and finalization artifacts without applying memory updates.
  - evidence artifact path(s): `stock_research/agent_runtime/orchestrators/memory_evaluation.py`, `agents/orchestrator/prompts/memory_evaluation.md`, `agents/orchestrator/specs/memory_evaluation.md`, `tests/test_agent_runtime.py`, `agents/runs/2026-05-10_manual-market-energy-storage/memory_evaluation/memory_evaluation.md`
  - status: active

- 2026-05-11:
  - decision/fact: Main orchestrator input aggregation now includes company research reports, market research reports, portfolio review reports, memory/evaluation reports, candidate verification results, human-review digest path, and open/approved human-review counts. This gives the final synthesis a high-level map across the full workflow.
  - evidence artifact path(s): `stock_research/agent_runtime/reports.py`, `stock_research/agent_runtime/orchestrators/main.py`, `agents/orchestrator/prompts/main.md`, `agents/orchestrator/specs/main.md`, `tests/test_agent_runtime.py`
  - status: active

- 2026-05-11:
  - decision/fact: Human review is digest-first and asynchronous. `agents/human_review_digest.md` is the primary user-facing inbox, `agents/human_review_queue.md` is durable state, portfolio/memory/candidate reports are deeper context, and Codex chat is the canonical approval path. Email/app notifications may summarize the digest later, but email should not become an approval source until a strict ingestion workflow is built and tested.
  - evidence artifact path(s): `docs/descriptions/human_review_operating_model.md`, `docs/descriptions/human_interaction_workflow.md`, `docs/plans/investment_agent_backlog.md`, `docs/plans/openai_agents_sdk_orchestration_backlog.md`
  - status: active

- 2026-05-11:
  - decision/fact: Weekly-style company research now has a deterministic opportunity-assessment lane and final digest. `opportunity_assessment` synthesizes financials, Exa news/company context, SEC filings, Grok/X sentiment, and risk signals into a reviewable expert-opinion report; `final_digest.md` is the concise human-facing report surface and fallback when live SDK main orchestration is unavailable.
  - evidence artifact path(s): `stock_research/opportunity_assessment.py`, `stock_research/weekly_digest.py`, `stock_research/agent_runtime/specialists/opportunity.py`, `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AMZN_opportunity_assessment.md`, `agents/runs/2026-05-16_weekly/final_digest.md`, `agents/runs/2026-05-16_weekly/orchestration_report.md`, `docs/descriptions/openai_agents_sdk_orchestration.md`
  - status: active

- 2026-05-11:
  - decision/fact: Weekly final digests and opportunity assessments now have deterministic quality gates for required evidence links/source ids, readable financial formatting, Grok/X social-signal labeling, direct trade-language blocking, and taxonomy-only conflict handling. `run-weekly --write` also refreshes `agents/human_review_digest.md` and includes open-review next actions.
  - evidence artifact path(s): `stock_research/weekly_digest.py`, `stock_research/opportunity_assessment.py`, `stock_research/report_formatting.py`, `stock_research/scheduled_runner.py`, `tests/test_weekly_digest.py`, `tests/test_opportunity_assessment.py`, `tests/test_scheduled_runner.py`, `agents/runs/2026-05-16_weekly/final_digest.md`, `agents/human_review_digest.md`
  - status: active

- 2026-05-12:
  - decision/fact: Structural validation is insufficient for this repo. The AMZN report passed earlier gates but failed the user's investor-usefulness standard because it reduced Grok/X and Exa outputs to status labels and internal chores. Future final digests/opportunity reports must surface concrete X/community narratives, bull/bear arguments, accounts/posts, hype/noise, verified-vs-speculative separation, source-backed developments, and clear research decisions.
  - evidence artifact path(s): `docs/scratchpads/openai_agents_sdk_orchestration_scratchpad.md`, `docs/plans/investment_agent_backlog.md`, `docs/plans/openai_agents_sdk_orchestration_backlog.md`, `agents/memory/evaluation_metrics.md`, `stock_research/opportunity_assessment.py`, `stock_research/weekly_digest.py`, `agents/runs/2026-05-16_weekly/final_digest.md`
  - status: active

- 2026-05-12:
  - decision/fact: Manual market-research reports now include a richer investor insight report section. The human-facing industry/theme report should include executive read, industry/theme context, X/community pulse, trend evolution, candidate pipeline, non-obvious/contrarian angles, decision table, and explicit approve/reject/request-more-research choices.
  - evidence artifact path(s): `stock_research/market_research_runner.py`, `tests/test_market_research_runner.py`, `agents/runs/2026-05-10_manual-market-energy-storage/market_research/grid_scale_energy_storage_manual_market_research.md`
  - status: active

- 2026-05-12:
  - decision/fact: Fresh live Grok/X market discovery must preserve full raw Grok output in human-facing reports when evidence packet claims are truncated. Reports should expose X pulse, trend evolution, bull/bear narratives, candidate follow-up, investor scorecard, hype/noise/rumors, and verification tasks. Provider artifact and packet ids are compacted with stable hashes so long topics/run ids do not break Windows path length limits.
  - evidence artifact path(s): `stock_research/providers/exa.py`, `stock_research/providers/xai_grok.py`, `stock_research/market_research_runner.py`, `agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/ai_semiconductor_supply_chain_advanced_packaging_manual_market_research.md`, `agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md`, `agents/human_review_digest.md`
  - status: active

- 2026-05-12:
  - decision/fact: Market discovery now groups repeated Grok/X multi-ticker basket leads into concise thematic review items before writing candidate review and human-review queue rows. When a candidate review is regenerated for the same run, stale open rows for that run are marked `superseded` before replacement rows are appended, preserving audit history without keeping stale review decisions active.
  - evidence artifact path(s): `stock_research/candidate_review.py`, `stock_research/market_research_runner.py`, `stock_research/human_review_digest.py`, `tests/test_market_research_runner.py`, `tests/test_human_review_digest.py`, `agents/runs/2026-05-12_manual-market-ai-semiconductor-supply-chain/market_research/candidate_review.md`, `agents/human_review_digest.md`
  - status: active

- 2026-05-12:
  - decision/fact: Opportunity assessments now include a richer investor insight report section. The human-facing company report should include executive read, company/industry context, thesis/trend change, Grok/X expert-community split, non-obvious insights, valuation/analyst target context, peer context, decision table, and next research questions.
  - evidence artifact path(s): `stock_research/opportunity_assessment.py`, `stock_research/weekly_digest.py`, `tests/test_opportunity_assessment.py`, `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AMZN_opportunity_assessment.md`, `agents/runs/2026-05-16_weekly/final_digest.md`
  - status: active

- 2026-05-15:
  - decision/fact: The AMZN opportunity-assessment structure and detail level is accepted as the current target for human-facing company reports. Final digests should stay concise as quick-read summaries with links to deeper opportunity assessments. Company research packets are primarily internal lane/coverage artifacts.
  - evidence artifact path(s): `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AMZN_opportunity_assessment.md`, `agents/runs/2026-05-16_weekly/final_digest.md`, `docs/HUMAN_USAGE_GUIDE.md`
  - status: active

- 2026-05-15:
  - decision/fact: Routine source-backed company-file factual updates should not normally require user approval. The target UX is scoped auto-apply plus FYI change summaries; thesis changes, opinion changes, stock moves, strategy changes, and buy/sell/position-size decisions remain approval-gated.
  - evidence artifact path(s): `docs/descriptions/human_review_operating_model.md`, `docs/descriptions/human_interaction_workflow.md`, `docs/plans/investment_agent_backlog.md`, `stock_research/human_review_digest.py`
  - status: active

- 2026-05-15:
  - decision/fact: Research artifact hygiene needs an archive/index lifecycle. Active knowledge should be promoted into stock files, category state, market research, and strategy files; old non-active run artifacts should be movable to an indexed archive rather than staying in the active working surface forever.
  - evidence artifact path(s): `docs/descriptions/artifact_lifecycle_and_hygiene.md`, `docs/plans/investment_agent_backlog.md`, `docs/descriptions/repo_map.md`
  - status: active

- 2026-05-16:
  - decision/fact: Research artifact hygiene is implemented with inventory, archive proposals, and guarded archive moves. Use `artifact-hygiene inventory --write` for `archive/research_index.md`; run finalization writes `archive_proposals.md`; use `artifact-hygiene archive --write` to move only eligible stale markdown artifacts into `archive/runs/`.
  - evidence artifact path(s): `stock_research/artifact_hygiene.py`, `stock_research/run_finalization.py`, `archive/research_index.md`, `archive/archive_move_report.md`, `agents/runs/2026-05-16_weekly/archive_proposals.md`
  - status: active

- 2026-05-16:
  - decision/fact: Category state updates are implemented. Use `python -m stock_research category-state update --run-id RUN_ID --write`; weekly runs now refresh holdings, monitoring, and rejected state files with source-linked automated summary rows.
  - evidence artifact path(s): `stock_research/category_state_updater.py`, `stock_research/scheduled_runner.py`, `stock_tracking/current_holdings/current_holdings_state.md`, `stock_tracking/monitoring/monitoring_state.md`, `stock_tracking/rejected/rejected_state.md`
  - status: active

- 2026-05-16:
  - decision/fact: Manual run-end review summaries are implemented for manual market research, candidate review, and SDK agent-runtime runs. They refresh `agents/human_review_digest.md` and write `agents/runs/{run_id}/human_review_digest_summary.md`.
  - evidence artifact path(s): `stock_research/run_end_review.py`, `stock_research/market_research_runner.py`, `stock_research/candidate_review.py`, `stock_research/cli.py`
  - status: active

- 2026-05-11:
  - decision/fact: The OpenAI Agents SDK weekly path completed successfully after API credit was added and runtime quality gates were tightened. The validation command for AMZN/AAPL is `python -m stock_research run-weekly --write --today 2026-05-11 --execute-providers --execute-analysis --execute-orchestrator --orchestrator-timeout-seconds 900`.
  - evidence artifact path(s): `agents/runs/2026-05-16_weekly/orchestration_report.md`, `agents/runs/2026-05-16_weekly/agent_runtime_main_orchestrator.md`, `stock_research/agent_runtime/reports.py`, `tests/test_agent_runtime.py`
  - status: active

- 2026-05-11:
  - decision/fact: Financial review should distinguish material financial metric conflicts from taxonomy/classification disagreements. A provider disagreement such as `Internet Retail` vs `Specialty Retail` is a watch item unless it affects material numeric metrics or thesis-critical classification.
  - evidence artifact path(s): `stock_research/financial_specialist.py`, `stock_research/financial_compare.py`, `agents/runs/2026-05-16_weekly/reports/financial_data_specialist/AMZN_financial_review.md`
  - status: active

- 2026-05-04:
  - decision/fact: Generated run JSON artifacts are local runtime output and should not be committed. Keep markdown run summaries/reports/finalization files as the reviewable artifacts; `.gitignore` now ignores run-root JSON, raw provider JSON, evidence packet JSON, and generated recurring-failure JSON.
  - evidence artifact path(s): `.gitignore`, `README.md`, `SETUP.md`, `docs/descriptions/run_summary_and_quality.md`
  - status: active

- 2026-05-04:
  - decision/fact: Manifest-driven Exa and xAI/Grok provider outputs use the manifest task id in artifact names and packet ids. This prevents same-provider/same-subject tasks from overwriting each other and lets quality checks verify task-specific packets.
  - evidence artifact path(s): `stock_research/providers/exa.py`, `stock_research/providers/xai_grok.py`, `stock_research/provider_runner.py`, `stock_research/quality_report.py`, `stock_research/memory_reflection.py`, `tests/test_exa_provider.py`, `tests/test_xai_grok_provider.py`, `tests/test_quality_report.py`
  - status: active

- 2026-05-04:
  - decision/fact: The deterministic company-news specialist is implemented with Exa contents follow-up. Use `python -m stock_research news contents-follow-up --ticker TICKER --run-id RUN_ID` after Exa company-news provider tasks, then `python -m stock_research news review --ticker TICKER --run-id RUN_ID`; search-highlight-only reviews stay `partial_review`.
  - evidence artifact path(s): `stock_research/company_news_specialist.py`, `stock_research/analysis_runner.py`, `stock_research/manifest.py`, `docs/descriptions/company_news_specialist.md`, `tests/test_company_news_specialist.py`, `agents/runs/2026-05-09_weekly/reports/company_news_specialist/AAPL_company_news_review.md`
  - status: active
