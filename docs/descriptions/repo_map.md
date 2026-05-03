# Repo Map

Last updated: 2026-05-03

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
- `docs/descriptions/evidence_schema.md`: shared source/evidence packet schema for all providers and specialists.
- `docs/descriptions/sec_edgar_provider.md`: SEC EDGAR provider behavior and setup.
- `docs/descriptions/exa_provider.md`: Exa search/contents provider behavior and best practices.
- `docs/descriptions/yfinance_provider.md`: yfinance provider behavior and setup.
- `docs/plans/investment_agent_backlog.md`: prioritized implementation backlog.
- `docs/plans/investment_agent_workflow_plan.md`: high-level implementation plan.
- `agents/orchestrator/`: future main orchestrator implementation.
- `agents/specialists/`: future specialist agent implementations.
- `agents/runs/`: future run artifacts.
- `agents/memory/`: future operational agent memory.

## Runtime Tooling

- `stock_research/`: stdlib-only deterministic Python core.
- `python -m stock_research summary`: print repo state summary.
- `python -m stock_research validate`: validate CSV schemas and required files.
- `python -m stock_research stale`: scan stock rows for stale dates.
- `python -m stock_research manifest`: generate weekly run manifest.
- `python -m stock_research classify-request "..."`
- `python -m stock_research add-request "..."`
- `python -m stock_research route-request "..."`: append and route a user request into target repo artifacts.
- `python -m stock_research evidence new ...`: create a provider-neutral evidence packet.
- `python -m stock_research evidence validate ...`: validate an evidence packet.
- `python -m stock_research sec company --ticker TICKER --run-id RUN_ID`: fetch SEC submissions into evidence artifacts.
- `python -m stock_research yfinance company --ticker TICKER --run-id RUN_ID`: fetch yfinance market-data snapshot artifacts.
- `python -m stock_research exa search --query "..." --subject-type TYPE --subject-id ID --run-id RUN_ID`: run Exa search into evidence artifacts.
- `python -m stock_research exa contents --url URL --subject-type TYPE --subject-id ID --run-id RUN_ID`: run Exa contents extraction into evidence artifacts.
- `python -m stock_research provider-tasks --manifest PATH`: dry-run provider tasks from a manifest.
- `python -m stock_research provider-tasks --manifest PATH --execute`: execute provider tasks from a manifest.
- `tests/`: unit tests for current deterministic core.

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
