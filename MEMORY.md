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
  - decision/fact: Approved initial data providers are Exa, X.com, SEC, yfinance, FMP, Polygon, and Alpha Vantage. Additional candidates may be evaluated before implementation.
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
