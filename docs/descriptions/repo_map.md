# Repo Map

Last updated: 2026-05-03

## Purpose

This file tells Codex, the orchestrator, and future agents where to find and update information.

## Start Here For Every Task

- `AGENTS.md`: repo-wide workflow rules.
- `MEMORY.md`: durable decisions and high-impact facts.
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
- `docs/plans/investment_agent_backlog.md`: prioritized implementation backlog.
- `docs/plans/investment_agent_workflow_plan.md`: high-level implementation plan.
- `agents/orchestrator/`: future main orchestrator implementation.
- `agents/specialists/`: future specialist agent implementations.
- `agents/runs/`: future run artifacts.
- `agents/memory/`: future operational agent memory.

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
