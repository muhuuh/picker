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

- `docs/HUMAN_USAGE_GUIDE.md`: concise human guide for using this repo through Codex chat.
- `docs/descriptions/repo_map.md`: where to find and update each kind of information.
- `docs/descriptions/human_interaction_workflow.md`: how user chat input becomes repo state.
- `docs/descriptions/human_review_operating_model.md`: how digest-first asynchronous human review and future notifications should work.
- `docs/plans/human_research_requests.md`: proactive user request queue.
- `agents/human_review_queue.md`: system-generated items needing user approval.
- `agents/memory/memory_index.md`: entry point for operational agent memory.
- `docs/descriptions/agent_memory_workflow.md`: memory read/write workflow and guardrails.
- `docs/descriptions/llm_memory_writer.md`: bounded LLM memory writer workflow.
- `docs/descriptions/scheduled_runner.md`: deterministic weekly workflow wrapper.
- `docs/descriptions/openai_agents_sdk_orchestration.md`: selected OpenAI Agents SDK runtime design.
- `docs/plans/openai_agents_sdk_orchestration_backlog.md`: dedicated SDK runtime backlog.
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
python -m stock_research run-weekly --write --execute-orchestrator
python -m stock_research run-weekly --write --execute-providers --execute-analysis --execute-orchestrator --orchestrator-timeout-seconds 300
```

`--execute-orchestrator` requires `OPENAI_API_KEY`. It now runs per-ticker company-research fanout for current-holding and monitoring tickers before main orchestration. If provider or analysis tasks are still dry-run and the SDK proposes alerts or file updates, the scheduled run is marked `needs_review` so stale artifacts cannot look like fresh research. If live SDK execution times out or errors, it writes a blocked reviewable artifact plus `run_metrics.md` instead of silently failing.

Inspect the OpenAI Agents SDK runtime registry without making live model calls:

```powershell
python -m stock_research agent-runtime list-agents
python -m stock_research agent-runtime smoke --run-id 2026-05-09_weekly
python -m stock_research agent-runtime run --run-id 2026-05-09_weekly
python -m stock_research agent-runtime run --run-id 2026-05-09_weekly --agent-id company_research_orchestrator --task "company research sub-orchestrator" --ticker AAPL
python -m stock_research agent-runtime run --run-id 2026-05-09_weekly --agent-id portfolio_review_orchestrator --task "portfolio review sub-orchestrator"
python -m stock_research agent-runtime run --run-id 2026-05-09_weekly --agent-id memory_evaluation_orchestrator --task "memory evaluation sub-orchestrator"
python -m stock_research agent-runtime validate-output --run-id 2026-05-09_weekly
python -m stock_research agent-runtime queue-proposals --run-id 2026-05-09_weekly --write --queue-review
python -m stock_research agent-runtime apply-proposal --run-id 2026-05-09_weekly --proposal-id ORP-0001
```

Run a manual market/industry/theme research loop while we are still iterating manually:

```powershell
python -m stock_research market-research run --topic "robotics suppliers in Europe" --subject-type industry
python -m stock_research market-research run --topic "robotics suppliers in Europe" --subject-type industry --write --execute-providers
python -m stock_research market-research run --topic "robotics suppliers in Europe" --subject-type industry --write --execute-providers --execute-orchestrator
python -m stock_research market-research candidate-review --run-id RUN_ID --write --queue-review
python -m stock_research market-research candidate-followup --run-id RUN_ID --review-id HRQ-0004 --write
python -m stock_research market-research candidate-verification-result --run-id RUN_ID --review-id HRQ-0004 --write
python -m stock_research market-research candidate-promote --run-id RUN_ID --review-id HRQ-0004 --write
python -m stock_research human-review digest --write
python -m stock_research human-review decide --set HRQ-0004=approved --note "Run verification." --write
```

This creates a manual manifest with Exa context, Exa company discovery, and Grok/X discovery lanes. With `--write`, it writes a reviewable market report and ignored candidate-lead JSON. Discovery gates keep Grok-only leads as verification tasks, enforce rejected-stock cooldowns, and require source ids plus verification labels. `candidate-review` groups duplicate/share-class leads and repeated Grok/X multi-ticker baskets, writes a review artifact, and can append duplicate-safe human-review queue rows without adding stocks to monitoring. Regenerated candidate-review rows for the same run supersede stale open rows. `human-review digest` writes a concise open-review summary to `agents/human_review_digest.md`, including the allowed human decisions: approve, reject, mark needs more research, or leave open. `human-review decide` records your approve/reject/more-research decisions in the queue and refreshes the digest; it does not run verification or edit stock files. `candidate-followup` only processes approved candidate-review rows and writes verification tasks. After the provider/analysis tasks run, `candidate-verification-result` consolidates provider coverage, specialist statuses, findings, and next actions. `candidate-promote` is the final approval-gated writer: it only adds a monitoring CSV row and company file when the HRQ row is approved, the candidate is a `monitoring_candidate`, and required verification artifacts exist.

Human review is digest-first. The user normally reviews `agents/human_review_digest.md` through Codex chat; portfolio review, memory/evaluation, candidate review, and proposal reports are deeper context. Future email/app notifications should summarize the digest, not act as approvals.

Run the OpenAI Agents SDK orchestrator over existing run artifacts:

```powershell
python -m stock_research agent-runtime run --run-id 2026-05-09_weekly --execute --write
```

This requires `OPENAI_API_KEY`. It writes local runtime report, trace-link, and run-metrics artifacts; it does not edit stock files.

`quality_findings: []` means the saved structured output passed deterministic runtime gates for summary/status shape, valid operational memory ids, exact file targets, source-backed update proposals, and traceable source artifacts. It does not mean the investment conclusion is automatically correct or trade-ready.

`agent-runtime queue-proposals` converts saved SDK proposals into `orchestrator_update_proposals.md` and optional human-review queue rows. It does not edit company files.

`agent-runtime apply-proposal` is the approval-gated company-file writer. It dry-runs by default, refuses proposals without a matching `approved` human-review queue row, and only edits the proposal's target company file when `--write` is passed.

Low-risk factual company-file sync is separate from thesis/status proposals:

```powershell
python -m stock_research company-file apply-factual-updates --run-id RUN_ID --write
python -m stock_research company-file apply-factual-updates --run-id RUN_ID --ticker AMZN --write --refresh
python -m stock_research category-state update --run-id RUN_ID --write
```

This reads opportunity-assessment artifacts, updates only automated factual/source/change-log sections in the target company file, and writes an FYI summary at `agents/runs/{run_id}/company_file_factual_updates.md`.
`category-state update` appends bucket-level summaries to holdings, monitoring, and rejected state files without overwriting human notes.

Artifact hygiene is indexed with:

```powershell
python -m stock_research artifact-hygiene inventory --write
python -m stock_research artifact-hygiene archive
python -m stock_research artifact-hygiene archive --write
```

Inventory writes `archive/research_index.md` with active, recent, review-blocked, archive-candidate, and archived run artifacts. Archive is dry-run by default; `--write` moves only eligible stale markdown reports into `archive/runs/` and refreshes the index.

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
- deterministic weekly runner that chains manifest, provider tasks, analysis tasks, summary, quality report, memory finalization, memory-writer review, and optional SDK orchestration.
- OpenAI Agents SDK runtime foundation: importable runtime package, main orchestrator builder, company-research sub-orchestrator, company-news specialist builder, company-search specialist builder, financial specialist builder, filing specialist builder, sentiment specialist builder, risk/thesis specialist builder, writer specialist builder, quality-review specialist builder, central registry, specialist-as-tool composition, typed context/output contracts, task-relevant memory injection, repo/memory inspection tools, prompt/spec files, and no-model-call smoke command.
- Company-research SDK sub-orchestrator for one ticker, with evidence lanes for financials, company news, filings, sentiment, company search, risk/thesis impact, writer proposals, and quality review, plus financial, company-news, company-search, filing, sentiment, risk/thesis, writer, and quality-review specialist fanout.
- Market-research SDK sub-orchestrator and manual runner for one industry/theme, with Exa industry/company discovery, Grok/X trend and rumor discovery, candidate discovery, quality-review specialist fanout, typed candidate leads, and discovery quality gates.
- Candidate verification result reporting after approved follow-up provider/analysis tasks.
- Portfolio-review SDK sub-orchestrator for holdings/monitoring/rejected buckets, human-review items, and candidate verification results.
- Memory/evaluation SDK sub-orchestrator for run metrics, quality reports, memory reflection, recurring failures, memory update drafts, memory writer review, and finalization.
- Main orchestrator aggregation packet that maps company, market, portfolio, memory/evaluation, candidate verification, and human-review artifacts before final synthesis.
- guarded OpenAI Agents SDK provider/analysis function tools that plan by default and require context permission for live side effects.
- live manual OpenAI Agents SDK orchestrator command over existing run artifacts, with local report, trace-link, and run-metrics artifacts.
- SDK local telemetry hooks for agent lifecycle, tool calls, LLM calls/usage when available, injected operational memory ids, and final-output reported memory ids.
- SDK timeout/error handling that writes blocked reviewable outputs and feeds runtime failures into memory reflection.
- function-first SDK fanout helper for independent agent tasks with per-task timeout, task-specific memory, partial-failure preservation, and aggregate metrics.
- opt-in scheduled OpenAI Agents SDK orchestration through `run-weekly --write --execute-orchestrator`, with per-ticker company-research fanout for current/monitoring tickers and freshness gating for dry-run provider/analysis inputs.
- deterministic SDK proposal review bridge: `agent-runtime queue-proposals --write --queue-review`.
- approval-gated SDK proposal writer: `agent-runtime apply-proposal --proposal-id ORP-0001 --write`.
- low-risk company-file factual updater with run-end FYI summary.
- category-state updater for holdings/monitoring/rejected bucket summaries.
- artifact inventory/index/archive commands for research-output hygiene.
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
- scheduled market-research fanout,
- OS/app scheduled execution,
- immediate research runs.
