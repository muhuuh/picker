# Repo Map

Last updated: 2026-05-07

## Purpose

This file tells Codex, the orchestrator, and future agents where to find and update information.

## Start Here For Every Task

- `AGENTS.md`: repo-wide workflow rules.
- `MEMORY.md`: durable decisions and high-impact facts.
- `README.md`: current repo purpose, commands, and implementation status.
- `SETUP.md`: local setup and verification commands.
- `docs/descriptions/`: architecture and behavior descriptions.
- `docs/scratchpads/`: short topic memory.
- `docs/plans/`: backlog, plans, and human input queue.

## Human Interaction

- `docs/descriptions/human_interaction_workflow.md`: how user chat input becomes repo state.
- `docs/plans/human_research_requests.md`: human input queue.
- `agents/human_review_queue.md`: system-generated items requiring user approval.

## Strategy

- `strategy/investment_strategy.md`: high-level investment approach.
- `strategy/screening_criteria.md`: candidate screening rules.
- `strategy/risk_rules.md`: risk and approval rules.
- `strategy/research_priorities.md`: recurring industries, themes, technologies, geographies, and ideas to research.

## Stock Tracking

- `stock_tracking/current_holdings/current_holdings.csv`: overview of current holdings.
- `stock_tracking/current_holdings/current_holdings_state.md`: portfolio-level state for current holdings.
- `stock_tracking/monitoring/monitoring.csv`: overview of monitored stocks.
- `stock_tracking/monitoring/monitoring_state.md`: state of the monitoring bucket.
- `stock_tracking/rejected/rejected.csv`: overview of rejected stocks and cooldown dates.
- `stock_tracking/rejected/rejected_state.md`: state of the rejected bucket.
- `stock_tracking/stock_info_files/`: detailed company files.
- `docs/templates/company_stock_info_template.md`: template for company files.
- `docs/templates/stock_tracking_csv_schema.md`: CSV schema documentation.

## Market Research

- `market_research/industries/`: industry-level research and candidate discovery.
- `market_research/themes/`: cross-industry technology/theme tracking.
- `market_research/macro/`: macro, policy, rates, inflation, currency, geopolitical context.
- `market_research/discovery/`: new stock ideas and discovery outputs.

## Agent Architecture

- `docs/descriptions/investment_agent_workflow.md`: full planned automated workflow.
- `docs/descriptions/agent_memory_workflow.md`: operational memory read/write workflow.
- `docs/descriptions/llm_memory_writer.md`: bounded LLM memory writer workflow over memory update drafts.
- `docs/descriptions/scheduled_runner.md`: deterministic weekly workflow wrapper.
- `docs/descriptions/openai_agents_sdk_orchestration.md`: selected OpenAI Agents SDK runtime design.
- `docs/plans/openai_agents_sdk_orchestration_backlog.md`: dedicated backlog for OpenAI Agents SDK runtime implementation.
- `docs/scratchpads/openai_agents_sdk_orchestration_scratchpad.md`: dedicated scratchpad for SDK orchestration findings and decisions.
- `docs/descriptions/evidence_schema.md`: shared source/evidence packet schema for all providers and specialists.
- `docs/descriptions/sec_edgar_provider.md`: SEC EDGAR provider behavior and setup.
- `docs/descriptions/exa_provider.md`: Exa search/contents provider behavior and best practices.
- `docs/descriptions/xai_grok_provider.md`: xAI Grok x_search provider behavior and setup.
- `docs/descriptions/yfinance_provider.md`: yfinance provider behavior and setup.
- `docs/descriptions/fmp_provider.md`: FMP market-data/fundamentals provider behavior and setup.
- `docs/descriptions/polygon_provider.md`: Polygon/Massive U.S. ticker/OHLC provider behavior and setup.
- `docs/descriptions/alpha_vantage_provider.md`: Alpha Vantage quote/overview provider behavior and setup.
- `docs/descriptions/financial_compare.md`: deterministic financial provider comparison behavior.
- `docs/descriptions/financial_data_specialist.md`: deterministic financial-data specialist review behavior.
- `docs/descriptions/company_news_specialist.md`: deterministic company-news specialist review behavior.
- `docs/descriptions/analysis_task_runner.md`: deterministic analysis-task runner behavior.
- `docs/descriptions/run_summary_and_quality.md`: deterministic run summary and quality report behavior.
- `docs/plans/investment_agent_backlog.md`: prioritized implementation backlog.
- `docs/plans/investment_agent_workflow_plan.md`: high-level implementation plan.
- `agents/orchestrator/`: future main orchestrator implementation.
- `agents/specialists/`: future specialist agent implementations.
- `agents/runs/`: future run artifacts.
  - Generated JSON/raw/evidence artifacts are local runtime output and ignored by Git.
  - Markdown run summaries, quality reports, reflections, and finalization reports are the reviewable artifacts.
- `agents/memory/`: operational agent memory.
- `agents/memory/memory_index.md`: entry point for task-relevant memory loading.
- `agents/memory/orchestrator_lessons.md`: orchestration and routing lessons.
- `agents/memory/source_quality.md`: provider/source reliability memory.
- `agents/memory/specialist_playbooks.md`: procedural memory for specialist agents.
- `agents/memory/evaluation_metrics.md`: run-quality and learning-loop memory.
- `agents/memory/deprecated_memory.md`: superseded or wrong lessons that should not be reintroduced.

## Runtime Tooling

- `stock_research/`: stdlib-only deterministic Python core.

Runtime commands are thin handles around importable Python functions. The preferred implementation boundary is:

```text
core Python function -> deterministic workflow / SDK tool wrapper -> optional CLI
```

Use CLI commands for manual operation, scheduler entrypoints, validation, smoke tests, and approval-gated side effects. Do not use CLI subprocesses as the normal internal integration between deterministic workflows and SDK tools.

- `python -m stock_research summary`: print repo state summary.
- `python -m stock_research validate`: validate CSV schemas and required files.
- `python -m stock_research stale`: scan stock rows for stale dates.
- `python -m stock_research manifest`: generate weekly run manifest.
- `python -m stock_research memory summary`: summarize operational memory.
- `python -m stock_research memory validate`: validate operational memory files and item fields.
- `python -m stock_research memory context --task TASK`: print task-relevant memory files and active lessons.
- `python -m stock_research memory add ...`: append a schema-valid operational memory item.
- `python -m stock_research memory deprecate --id ITEM_ID --reason "..."`: mark a memory item deprecated and record why.
- `python -m stock_research memory reflect-run --run-id RUN_ID --write`: generate post-run memory reflection artifacts and memory update proposals.
- `python -m stock_research memory recurring-failures --write`: detect repeated reflection issues across runs.
- `python -m stock_research memory draft-updates --run-id RUN_ID --write`: convert reflection proposals into schema-valid memory update drafts.
- `python -m stock_research memory writer-prompt --run-id RUN_ID --write`: write the bounded memory-writer prompt artifacts for review.
- `python -m stock_research memory writer-review --run-id RUN_ID --write`: run deterministic writer review over memory update drafts.
- `python -m stock_research memory writer-review --run-id RUN_ID --execute --write --update-drafts`: run OpenAI-backed structured writer review and update draft artifacts.
- `python -m stock_research memory apply-updates --run-id RUN_ID --proposal-id PROPOSAL_ID`: apply an approved ready memory draft.
- `python -m stock_research memory prompt-context --task TASK`: print prompt-ready operational memory for future specialist injection.
- `python -m stock_research memory finalize-run --run-id RUN_ID`: write reflection, recurring-failure, and run finalization artifacts.
- `python -m stock_research classify-request "..."`
- `python -m stock_research add-request "..."`
- `python -m stock_research route-request "..."`: append and route a user request into target repo artifacts.
- `python -m stock_research evidence new ...`: create a provider-neutral evidence packet.
- `python -m stock_research evidence validate ...`: validate an evidence packet.
- `python -m stock_research sec company --ticker TICKER --run-id RUN_ID`: fetch SEC submissions into evidence artifacts.
- `python -m stock_research yfinance company --ticker TICKER --run-id RUN_ID`: fetch yfinance market-data snapshot artifacts.
- `python -m stock_research fmp company --ticker TICKER --run-id RUN_ID`: fetch FMP quote/profile/TTM metrics artifacts.
- `python -m stock_research polygon company --ticker TICKER --run-id RUN_ID`: fetch Polygon/Massive ticker details and previous-day OHLC artifacts.
- `python -m stock_research alpha-vantage company --ticker TICKER --run-id RUN_ID`: fetch Alpha Vantage quote/overview artifacts.
- `python -m stock_research financial compare --ticker TICKER --run-id RUN_ID`: compare financial provider packets into one reconciliation packet.
- `python -m stock_research financial review --ticker TICKER --run-id RUN_ID`: review a financial_compare packet into a specialist evidence packet and markdown report.
- `python -m stock_research news contents-follow-up --ticker TICKER --run-id RUN_ID`: run Exa contents extraction for high-value company-news URLs.
- `python -m stock_research news review --ticker TICKER --run-id RUN_ID`: review an Exa company-news packet into a specialist evidence packet and markdown report.
- `python -m stock_research exa search --query "..." --subject-type TYPE --subject-id ID --run-id RUN_ID`: run Exa search into evidence artifacts.
- `python -m stock_research exa contents --url URL --subject-type TYPE --subject-id ID --run-id RUN_ID`: run Exa contents extraction into evidence artifacts.
- `python -m stock_research xai x-search --ticker TICKER --subject-type company --subject-id TICKER --run-id RUN_ID`: run Grok x_search into social evidence artifacts.
- `python -m stock_research provider-tasks --manifest PATH`: dry-run provider tasks from a manifest.
- `python -m stock_research provider-tasks --manifest PATH --execute`: execute provider tasks from a manifest.
- `python -m stock_research analysis-tasks --manifest PATH`: dry-run analysis tasks from a manifest.
- `python -m stock_research analysis-tasks --manifest PATH --execute`: execute analysis tasks from a manifest.
- `python -m stock_research run-summary --run-id RUN_ID --write`: write run_summary artifacts from run evidence.
- `python -m stock_research quality-report --run-id RUN_ID --write`: write quality_report artifacts from run evidence.
- `python -m stock_research run-weekly`: dry-run the deterministic weekly workflow wrapper.
- `python -m stock_research run-weekly --write --execute-providers --execute-analysis`: execute and persist the deterministic weekly workflow without SDK synthesis.
- `python -m stock_research run-weekly --write --execute-orchestrator --orchestrator-timeout-seconds 300`: opt into OpenAI Agents SDK synthesis over written run artifacts. Requires `OPENAI_API_KEY`; actionable output from dry-run provider/analysis inputs is marked `needs_review`.
- `python -m stock_research run-weekly --write --execute-providers --execute-analysis --execute-orchestrator --orchestrator-timeout-seconds 300`: execute fresh provider/analysis tasks and then run SDK synthesis.
- `python -m stock_research agent-runtime list-agents`: list registered OpenAI Agents SDK orchestrators and specialists.
- `python -m stock_research agent-runtime smoke --run-id RUN_ID`: build the SDK runtime context and main orchestrator without calling a live model.
- `python -m stock_research agent-runtime run --run-id RUN_ID --execute --write`: run the main SDK orchestrator over existing artifacts and write runtime report/metrics artifacts without editing stock files.
- `python -m stock_research agent-runtime validate-output --run-id RUN_ID`: validate a saved SDK runtime output without calling a model.
- `python -m stock_research agent-runtime queue-proposals --run-id RUN_ID --write --queue-review`: convert saved SDK file-update proposals into `orchestrator_update_proposals.md` and duplicate-safe human-review queue rows.
- `python -m stock_research agent-runtime apply-proposal --run-id RUN_ID --proposal-id ORP-0001 --write`: apply one approved SDK proposal to its target company file through the deterministic approval-gated writer.
- `tests/`: unit tests for current deterministic core.

## OpenAI Agents SDK Runtime Planning

- Selected framework: OpenAI Agents SDK.
- Dedicated plan: `docs/plans/openai_agents_sdk_orchestration_backlog.md`.
- Dedicated scratchpad: `docs/scratchpads/openai_agents_sdk_orchestration_scratchpad.md`.
- Runtime code location: `stock_research/agent_runtime/`.
- Prompt/spec locations: `agents/orchestrator/` and `agents/specialists/`.
- Do not add broad LLM orchestration code without following the dedicated backlog.
- First runtime foundation is implemented under `stock_research/agent_runtime/`.
- SDK repo/memory tools live in `stock_research/agent_runtime/tools/repo_tools.py` and wrap Python functions directly for repo map, run summary, quality report, memory context, evidence packet index, run markdown, and stock CSV loading.
- SDK provider/analysis tools live in `stock_research/agent_runtime/tools/provider_tools.py` and `stock_research/agent_runtime/tools/analysis_tools.py`; they plan by default and block live side effects unless runtime context explicitly grants execution.
- SDK local telemetry lives in `stock_research/agent_runtime/tracing.py`; `run_metrics.md` records agent/tool/LLM rows plus injected and reported operational memory ids and runner-level timeout/error status.
- Post-run reflection in `stock_research/memory_reflection.py` reads `run_metrics.md` and turns SDK runtime failures or missing metrics into reflection issues.
- SDK fanout infrastructure lives in `stock_research/agent_runtime/fanout.py`; it is for future sub-orchestrators and is not yet wired into scheduled `run-weekly`.
- Live orchestration from `run-weekly` is available behind `--execute-orchestrator`; it is opt-in and freshness-gated.
- SDK output proposals are reviewable through `agents/runs/{run_id}/orchestrator_update_proposals.md` and `agents/human_review_queue.md`; company files are not edited by this bridge.
- Approved SDK proposals can be applied only through `agent-runtime apply-proposal`, which refuses unapproved review rows and validates the target is an existing file under `stock_tracking/stock_info_files/`.

## Where To Put Common User Requests

| User request | Primary update | Secondary update |
| --- | --- | --- |
| Research specific stocks | `docs/plans/human_research_requests.md` | `stock_tracking/monitoring/`, company files |
| Track an industry | `market_research/industries/` | `strategy/research_priorities.md` |
| Track a technology/theme | `market_research/themes/` | `strategy/research_priorities.md`, strategy files |
| Change strategy | `strategy/` | `MEMORY.md` if durable/high-impact |
| Review alerts | `agents/human_review_queue.md` | latest run summary/category state files |
| Move stock status | relevant `stock_tracking/` CSV/state | company file, human review queue if needed |
| Run research now | `docs/plans/human_research_requests.md` | future `agents/runs/` manual run artifact |
