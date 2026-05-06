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
- `agents/memory/memory_index.md`: entry point for operational agent memory.
- `docs/descriptions/agent_memory_workflow.md`: memory read/write workflow and guardrails.
- `docs/descriptions/llm_memory_writer.md`: bounded LLM memory writer workflow.
- `docs/descriptions/scheduled_runner.md`: deterministic weekly workflow wrapper.
- `strategy/research_priorities.md`: recurring research priorities.
- `stock_tracking/`: holdings, monitoring, rejected stocks, and company files.

## Python Commands

Run from the repo root:

```powershell
python -m stock_research summary
python -m stock_research validate
python -m stock_research stale
python -m stock_research manifest
python -m stock_research memory summary
python -m stock_research memory validate
```

Write a weekly manifest:

```powershell
python -m stock_research manifest --write
```

Dry-run planned provider tasks from a manifest:

```powershell
python -m stock_research provider-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json
```

Execute planned provider tasks explicitly:

```powershell
python -m stock_research provider-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --execute
```

Dry-run or execute planned analysis tasks from a manifest:

```powershell
python -m stock_research analysis-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json
python -m stock_research analysis-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --execute
```

Write deterministic run summary and quality report artifacts:

```powershell
python -m stock_research run-summary --run-id 2026-05-09_weekly --write
python -m stock_research quality-report --run-id 2026-05-09_weekly --write
```

Run the deterministic weekly workflow wrapper:

```powershell
python -m stock_research run-weekly
python -m stock_research run-weekly --write
python -m stock_research run-weekly --write --execute-providers --execute-analysis
```

Generated run JSON, raw provider JSON, and evidence packet JSON are local runtime artifacts ignored by Git. Commit the markdown summaries/reports and source/docs changes, not the generated JSON blobs.

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

Fetch yfinance market data into an evidence packet:

```powershell
python -m stock_research yfinance company --ticker AAPL --run-id 2026-05-09_weekly
```

Fetch paid/free market-data cross-check providers into evidence packets:

```powershell
python -m stock_research fmp company --ticker AAPL --run-id 2026-05-09_weekly
python -m stock_research polygon company --ticker AAPL --run-id 2026-05-09_weekly
python -m stock_research alpha-vantage company --ticker AAPL --run-id 2026-05-09_weekly
```

FMP, Polygon/Massive, and Alpha Vantage require `FMP_API_KEY`, `POLYGON_API_KEY`, and `ALPHA_VANTAGE_API_KEY` respectively. `MASSIVE_API_KEY` is also accepted for Polygon/Massive.

Compare financial provider packets into one reconciliation packet:

```powershell
python -m stock_research financial compare --ticker AAPL --run-id 2026-05-09_weekly
```

Run the deterministic financial-data specialist review:

```powershell
python -m stock_research financial review --ticker AAPL --run-id 2026-05-09_weekly
```

Run the deterministic company-news specialist review:

```powershell
python -m stock_research news contents-follow-up --ticker AAPL --run-id 2026-05-09_weekly
python -m stock_research news review --ticker AAPL --run-id 2026-05-09_weekly
```

The review treats Exa search highlights/headlines as `partial_review` until selected high-value URLs have successful Exa contents extraction.

Run Exa search or content extraction into evidence packets:

```powershell
python -m stock_research exa search --mode news --query "semiconductor supply chain disruptions Europe" --subject-type industry --subject-id semiconductors --run-id 2026-05-09_weekly
python -m stock_research exa contents --url https://example.com/article --subject-type company --subject-id AAPL --run-id 2026-05-09_weekly --highlights-query "investment relevance and risks"
```

Exa requires `EXA_API_KEY` in `.env` or `--api-key`.

Run Grok x_search into social evidence packets:

```powershell
python -m stock_research xai x-search --ticker AMD --company-name "Advanced Micro Devices" --subject-type company --subject-id AMD --run-id 2026-05-09_weekly
```

xAI/Grok requires `XAI_API_KEY` in `.env` or `--api-key`.

Add a request to the human input queue:

```powershell
python -m stock_research add-request "Look into European grid infrastructure suppliers" --priority high
```

Add and route a request into target artifacts:

```powershell
python -m stock_research route-request "Research ASML, TSM, AMD, and SAP" --priority high
```

Inspect operational agent memory:

```powershell
python -m stock_research memory summary
python -m stock_research memory validate
python -m stock_research memory context --task financial
python -m stock_research memory reflect-run --run-id 2026-05-09_weekly --write
python -m stock_research memory recurring-failures --write
python -m stock_research memory draft-updates --run-id 2026-05-09_weekly --write
python -m stock_research memory writer-review --run-id 2026-05-09_weekly --write
python -m stock_research memory writer-review --run-id 2026-05-09_weekly --execute --write --update-drafts
python -m stock_research memory apply-updates --run-id 2026-05-09_weekly --proposal-id PROPOSAL_ID
python -m stock_research memory prompt-context --task "news specialist"
python -m stock_research memory finalize-run --run-id 2026-05-09_weekly
```

Add or deprecate structured operational memory:

```powershell
python -m stock_research memory add --type procedural --scope orchestrator --trigger-source "..." --lesson "..." --use-when "..." --do-not-use-when "..." --evidence "..." --owner "..." --next-review 2026-06-01
python -m stock_research memory deprecate --id ITEM_ID --reason "..."
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
- deterministic provider-task planner and dry-run-by-default provider task runner,
- deterministic analysis-task planner and dry-run-by-default analysis task runner,
- deterministic run summary generator,
- deterministic quality report generator,
- generated run JSON ignore rules, with markdown run summaries/reports kept as the reviewable artifacts.
- deterministic operational memory loader, validator, summary, and task-context selector.
- deterministic operational memory add/deprecate commands.
- deterministic post-run memory reflection and memory update proposal generator.
- deterministic recurring failure detector across reflected runs.
- deterministic memory update draft/apply workflow for reflection proposals.
- bounded LLM memory writer prompt/review workflow for memory update drafts.
- prompt-ready operational memory context for future specialist injection.
- deterministic run finalization command for reflection, recurring-failure, and finalization artifacts.
- deterministic weekly runner that chains manifest, provider tasks, analysis tasks, summary, quality report, memory finalization, and memory-writer review up to the agent-framework decision boundary.
- deterministic human request classifier and queue appender.
- deterministic request router for stock, industry, theme, strategy, alert-review, manual-run, and status-move requests.
- provider-neutral evidence packet schema and JSON artifact writer.
- SEC EDGAR submissions provider with optional companyfacts retrieval, live-smoke-tested against AAPL.
- yfinance market-data snapshot provider.
- FMP company quote/profile/TTM metrics provider.
- Polygon/Massive U.S. ticker reference and previous-day OHLC provider.
- Alpha Vantage quote/overview provider.
- deterministic financial provider comparison layer.
- deterministic financial-data specialist review layer.
- deterministic company-news specialist review layer.
- automatic Exa contents follow-up for company-news reviews.
- Exa search and contents provider tools.
- xAI Grok x_search provider tools.
- structured operational agent memory under `agents/memory/`.

Not implemented yet:

- macro provider integrations,
- LLM specialist agents,
- LLM orchestrator runtime,
- OS/app scheduled execution,
- immediate research runs.
