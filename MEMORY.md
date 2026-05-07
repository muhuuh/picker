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
