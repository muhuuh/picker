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

- 2026-05-03:
  - decision/fact: Direct X.com API recent search/counts was the wrong implementation path and is superseded. The repo should use xAI/Grok with built-in `x_search` via `XAI_API_KEY` for X sentiment/latest-news research.
  - evidence artifact path(s): `stock_research/providers/xai_grok.py`, `docs/descriptions/xai_grok_provider.md`, `tests/test_xai_grok_provider.py`, `stock_research/manifest.py`, `stock_research/provider_runner.py`
  - status: active

- 2026-05-03:
  - decision/fact: xAI/Grok live `x_search` smoke test passed for AMD with a 2026-05-01 to 2026-05-03 window. The tool wrote raw Grok output and a validated provider-neutral evidence packet.
  - evidence artifact path(s): `agents/runs/2026-05-09_weekly/raw/xai_grok/x_search_amd.json`, `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_xai_grok_company_amd.json`
  - status: active
