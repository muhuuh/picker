# Stock Research

This repo is for automated stock tracking, investment research, and agent workflow development.

The current implementation is a deterministic Python foundation. It reads the repo state, validates stock tracking files, loads human research requests and research priorities, checks rejected-stock cooldown state, scans for stale tracking rows, and builds a weekly run manifest.

## Current Scope

- Markets: US and Europe.
- Cadence: weekly deep research on Saturday.
- Human review rhythm: Sunday review and planning.
- Human interface: Codex chat first; durable state is stored in repo files.
- Rejected stocks: 6-week cooldown before they can surface again unless manually overridden.

## Important Files

- `docs/descriptions/repo_map.md`: where to find and update each kind of information.
- `docs/descriptions/human_interaction_workflow.md`: how user chat input becomes repo state.
- `docs/plans/human_research_requests.md`: proactive user request queue.
- `agents/human_review_queue.md`: system-generated items needing user approval.
- `strategy/research_priorities.md`: recurring research priorities.
- `stock_tracking/`: holdings, monitoring, rejected stocks, and company files.

## Python Commands

Run from the repo root:

```powershell
python -m stock_research summary
python -m stock_research validate
python -m stock_research stale
python -m stock_research manifest
```

Write a weekly manifest:

```powershell
python -m stock_research manifest --write
```

Classify a natural-language user request:

```powershell
python -m stock_research classify-request "Research ASML, TSM, AMD, and SAP"
python -m stock_research route-request "Research ASML, TSM, AMD, and SAP" --priority high
```

Create and validate evidence packets:

```powershell
python -m stock_research evidence new --provider exa --subject-type industry --subject-id "European defense" --run-id 2026-05-09_weekly
python -m stock_research evidence validate agents/runs/2026-05-09_weekly/evidence_packets/PACKET.json
```

Fetch SEC EDGAR submissions into an evidence packet:

```powershell
python -m stock_research sec company --ticker AAPL --run-id 2026-05-09_weekly
```

SEC does not require an API key, but it does require a declared `User-Agent`. Set `SEC_USER_AGENT` in `.env` or pass `--user-agent`.

Add a request to the human input queue:

```powershell
python -m stock_research add-request "Look into European grid infrastructure suppliers" --priority high
```

Add and route a request into target artifacts:

```powershell
python -m stock_research route-request "Research ASML, TSM, AMD, and SAP" --priority high
```

## Tests

```powershell
python -m unittest discover -s tests
```

## Status

Implemented:

- repo state loader,
- CSV schema validator,
- stock-info file indexer,
- human input queue loader,
- research priorities loader,
- human review queue loader,
- rejected-stock cooldown summary,
- stale-data scanner,
- weekly run manifest generator,
- deterministic human request classifier and queue appender.
- deterministic request router for stock, industry, theme, strategy, alert-review, manual-run, and status-move requests.
- provider-neutral evidence packet schema and JSON artifact writer.
- SEC EDGAR submissions provider with optional companyfacts retrieval, live-smoke-tested against AAPL.

Not implemented yet:

- Exa, X.com/xAI, yfinance, FMP, Polygon, Alpha Vantage, and macro provider integrations,
- LLM specialist agents,
- orchestrator runtime,
- automated scheduled execution,
- immediate research runs.
