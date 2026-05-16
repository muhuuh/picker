# Setup

Last updated: 2026-05-15

## Requirements

- Python 3.10 or newer.
- `yfinance` is required for live yfinance market-data snapshots.
- `openai-agents` is required for the OpenAI Agents SDK runtime foundation.

Install declared dependencies:

```powershell
python -m pip install -e .
```

## Verify Python

```powershell
python --version
```

## Run From Repo Root

```powershell
cd C:\Users\valen\Documents\Code\stocks
python -m stock_research summary
python -m stock_research validate
python -m stock_research memory validate
python -m stock_research model-routing show --route main_orchestrator
python -m unittest discover -s tests
```

## Human Intake Routing

Classify a request without editing files:

```powershell
python -m stock_research classify-request "Research ASML, TSM, AMD, and SAP"
```

Append and route a request into durable repo artifacts:

```powershell
python -m stock_research route-request "Research ASML, TSM, AMD, and SAP" --priority high
```

## Evidence Packets

Create a provider-neutral evidence packet:

```powershell
python -m stock_research evidence new --provider provider_test --subject-type provider_test --subject-id smoke --run-id 2026-05-09_weekly
```

Validate a packet:

```powershell
python -m stock_research evidence validate agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_provider_test_provider_test_smoke.json
```

## Environment Variables

The deterministic core does not require API keys.

SEC EDGAR does not require an API key, but it does require a declared User-Agent:

```text
SEC_USER_AGENT="Stock Research your.email@example.com"
```

Use a real contact email or domain you control.

Exa requires an API key:

```text
EXA_API_KEY="..."
```

xAI Grok requires an API key:

```text
XAI_API_KEY="..."
```

Market-data cross-check providers require keys when used:

```text
FMP_API_KEY="..."
POLYGON_API_KEY="..."
ALPHA_VANTAGE_API_KEY="..."
```

`MASSIVE_API_KEY` is also accepted for Polygon/Massive.

Provider integrations planned later may use:

- Exa,
- xAI/Grok,
- OpenAI Agents SDK.

The bounded LLM memory writer requires OpenAI only when live execution is requested:

```text
OPENAI_API_KEY="..."
```

Keep secrets in `.env` or local environment variables. Do not commit `.env`.

Use `.env.example` as a local template.

## Model Routing

Model tiers and task routes live in `agents/model_routing.yaml`.

Inspect the resolved route:

```powershell
python -m stock_research model-routing show --route main_orchestrator
python -m stock_research model-routing show --route writer_specialist
python -m stock_research model-routing show --route xai_stock_sentiment
```

Precedence is explicit override, route-specific environment variable, tier environment variable, config file, then built-in fallback. Useful overrides:

```text
STOCK_RESEARCH_MODEL_MAIN_ORCHESTRATOR="..."
STOCK_RESEARCH_OPENAI_STRONG_MODEL="..."
STOCK_RESEARCH_OPENAI_FAST_MODEL="..."
STOCK_RESEARCH_XAI_GROK_MODEL="..."
```

Manual/Codex-supervised mode is different from API mode. Codex app/automation can use your configured Codex GPT-5.5 high environment to run repo commands, inspect reports, improve prompts, write final synthesis, and edit files. Python code in this repo cannot directly call the current Codex chat model internally; unattended SDK execution outside Codex must use routed API models through `OPENAI_API_KEY`.

## Codex App Automation

The first scheduled automation is managed by the Codex app:

```text
C:\Users\valen\.codex\automations\biweekly-holdings-and-monitoring-research\automation.toml
```

It runs every two weeks on Saturday at 08:00, starting 2026-05-16, from `C:\Users\valen\Documents\Code\stocks`.

The automation command is intentionally exact and lower-cost:

```powershell
C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis
```

This is Codex-supervised mode. It intentionally omits `--execute-orchestrator`, writes `agents/runs/{run_id}/codex_supervised_review_pack.md`, and expects Codex app automation to write `agents/runs/{run_id}/codex_supervised_review.md` after reading the pack and linked artifacts.

Codex automation sandbox rules live at:

```text
C:\Users\valen\.codex\rules\default.rules
```

Validate the rule before relying on the automation:

```powershell
codex execpolicy check --pretty --rules C:\Users\valen\.codex\rules\default.rules -- C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis
```

Expected result: `decision: allow`. Keep this narrow; do not allow broad Git/network commands or arbitrary Python module execution for the automation. The API SDK command with `--execute-orchestrator` remains a separate explicit benchmark/remote-mode path, not the default scheduled command.

## OpenAI Agents SDK Runtime

OpenAI Agents SDK is selected as the LLM orchestration framework. The package is declared in `pyproject.toml`, and the initial runtime foundation exists under `stock_research/agent_runtime/`. SDK tools wrap importable Python functions directly; CLI commands are only manual/scheduler/debug handles.

The main orchestrator currently exposes repo/memory inspection tools, `company_news_specialist`, `company_search_specialist`, `financial_specialist`, `filing_specialist`, `sentiment_specialist`, `risk_thesis_specialist`, `writer_specialist`, `quality_reviewer_specialist`, `exa_industry_specialist`, `grok_discovery_specialist`, and `discovery_specialist` as agent tools, and guarded provider/analysis SDK function tools. Provider and analysis tools plan by default and block live side effects unless the runtime context explicitly allows execution.

When SDK execution writes metrics, `run_metrics.md` includes local hook telemetry for agent lifecycle, tool calls, LLM usage when available, injected operational memory ids, final-output reported memory ids, and runner-level timeout/error status. It does not log raw prompts or raw tool payloads. Post-run memory reflection reads those metrics and flags SDK timeouts/errors as reviewable learning-loop issues.

`stock_research/agent_runtime/fanout.py` provides the code-level fanout helper for sub-orchestrators. It runs independent SDK agent tasks concurrently with task-specific memory, per-task timeout, and partial-failure preservation. API mode `run-weekly --write --execute-orchestrator` uses it for per-ticker company research; default Codex-supervised scheduled mode skips this API call and lets Codex synthesize from the deterministic review pack.

`company_research_orchestrator` is the first SDK sub-orchestrator. It can build a one-ticker company research packet, group evidence into financials/company-news/filings/sentiment/company-search/risk-thesis/writer/quality lanes, run financial, company-news, company-search, filing, sentiment, risk/thesis, writer, and quality-review specialist fanout, and preserve partial lanes as next-run tasks.

`market_research_orchestrator` is the first discovery sub-orchestrator. It can build an industry/theme market research packet, group evidence into Exa industry, Exa company discovery, Grok/X discovery, and candidate-synthesis lanes, and run Exa industry, Grok discovery, candidate discovery, and quality-review specialist fanout. Grok/X is required for niche trends, hype, rumors, and emerging ticker leads, but those leads must be verified elsewhere before promotion.

`portfolio_review_orchestrator` reviews current holdings, monitoring, rejected cooldowns, open/approved human-review items, and candidate verification results. It is a synthesis layer only: it does not trade, move stocks, or edit company files.

Human review is digest-first. `agents/human_review_digest.md` is the primary user-facing inbox; portfolio review, memory/evaluation, candidate review, and proposal reports are deeper context. The expected user flow is to review the digest through Codex chat and give explicit HRQ decisions. Future email/app notifications should summarize the digest, not directly approve actions.

`memory_evaluation_orchestrator` reviews run metrics, quality reports, memory reflection, recurring failures, memory update drafts, memory writer review, and finalization. It does not apply memory updates; approved memory writes still go through deterministic `memory apply-updates`.

The main orchestrator prompt now receives an aggregation packet that maps company research, market research, portfolio review, memory/evaluation, candidate verification, human-review digest, and review-count artifacts before final synthesis.

The manual market-research runner is the preferred near-term path for learning and prompt iteration:

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

It plans Exa context, Exa company-discovery, and Grok/X discovery lanes. With `--write`, it writes a markdown market report and ignored candidate-lead JSON under `agents/runs/RUN_ID/market_research/`. Candidate quality gates prevent Grok-only promotion, enforce rejected-stock cooldowns, and require source ids plus verification labels. The candidate-review command groups duplicate/share-class leads and repeated Grok/X multi-ticker baskets, optionally queues approval items in `agents/human_review_queue.md`, and marks stale regenerated open rows as `superseded`; it does not add stocks to monitoring. The human-review digest command writes a concise pending-review summary to `agents/human_review_digest.md`, including the allowed decisions: approve, reject, mark needs more research, or leave open. The human-review decide command records your queue decision and refreshes the digest; it does not run verification or edit stock files by itself. The candidate-followup command reads only approved candidate-review rows and writes provider/analysis verification tasks for the existing runners. The candidate-verification-result command consolidates provider coverage, specialist statuses, findings, and next actions after those tasks run. The candidate-promote command is approval-gated and verification-gated; it writes monitoring state only for an approved `monitoring_candidate` with required verification reports.

Planning files:

```text
docs/descriptions/openai_agents_sdk_orchestration.md
docs/plans/openai_agents_sdk_orchestration_backlog.md
docs/scratchpads/openai_agents_sdk_orchestration_scratchpad.md
```

Inspect the registry and build the main orchestrator without making live model calls:

```powershell
python -m stock_research agent-runtime list-agents
python -m stock_research agent-runtime smoke --run-id 2026-05-09_weekly
python -m stock_research agent-runtime run --run-id 2026-05-09_weekly
python -m stock_research agent-runtime run --run-id 2026-05-09_weekly --agent-id company_research_orchestrator --task "company research sub-orchestrator" --ticker AAPL
python -m stock_research agent-runtime run --run-id 2026-05-09_weekly --agent-id market_research_orchestrator --task "market research sub-orchestrator" --subject-type industry --subject-id european_grid_infrastructure --topic "European grid infrastructure"
python -m stock_research agent-runtime run --run-id 2026-05-09_weekly --agent-id portfolio_review_orchestrator --task "portfolio review sub-orchestrator"
python -m stock_research agent-runtime run --run-id 2026-05-09_weekly --agent-id memory_evaluation_orchestrator --task "memory evaluation sub-orchestrator"
python -m stock_research agent-runtime validate-output --run-id 2026-05-09_weekly
python -m stock_research agent-runtime queue-proposals --run-id 2026-05-09_weekly --write --queue-review
python -m stock_research agent-runtime apply-proposal --run-id 2026-05-09_weekly --proposal-id ORP-0001
```

Run the main orchestrator over existing artifacts:

```powershell
python -m stock_research agent-runtime run --run-id 2026-05-09_weekly --execute --write
```

This requires `OPENAI_API_KEY`. The command writes local runtime report, trace-link, and run-metrics artifacts. It does not edit stock files.

Validate a saved runtime output without calling the model:

```powershell
python -m stock_research agent-runtime validate-output --run-id 2026-05-09_weekly
```

Convert a saved runtime output into reviewable update proposals and human-review queue items:

```powershell
python -m stock_research agent-runtime queue-proposals --run-id 2026-05-09_weekly --write --queue-review
```

This writes `agents/runs/RUN_ID/orchestrator_update_proposals.md` and appends duplicate-safe review rows to `agents/human_review_queue.md`. It does not edit company files.

Dry-run an approved proposal application:

```powershell
python -m stock_research agent-runtime apply-proposal --run-id 2026-05-09_weekly --proposal-id ORP-0001
```

Apply it only after the matching `agents/human_review_queue.md` row is set to `approved`:

```powershell
python -m stock_research agent-runtime apply-proposal --run-id 2026-05-09_weekly --proposal-id ORP-0001 --write
```

This command refuses open/rejected/missing review rows and only edits the proposal target company file.

Run the SDK orchestrator from the weekly wrapper only when you explicitly want API mode:

```powershell
python -m stock_research run-weekly --write --execute-orchestrator
python -m stock_research run-weekly --write --execute-providers --execute-analysis --execute-orchestrator --orchestrator-timeout-seconds 300
```

`--execute-orchestrator` requires `OPENAI_API_KEY` and `--write`. When provider or analysis tasks are dry-run, actionable SDK output is marked `needs_review` until fresh deterministic execution runs.

When SDK orchestration is enabled, the weekly wrapper runs company-research fanout for all current-holding and monitoring tickers before the main orchestrator and writes per-ticker reports under `agents/runs/RUN_ID/company_research/`.

For the default local Codex-supervised workflow, use `run-weekly --write --execute-providers --execute-analysis`, then have Codex read `codex_supervised_review_pack.md` and write `codex_supervised_review.md`.

## SEC EDGAR

Fetch SEC submissions:

```powershell
python -m stock_research sec company --ticker AAPL --run-id 2026-05-09_weekly
```

Include XBRL company facts:

```powershell
python -m stock_research sec company --ticker AAPL --run-id 2026-05-09_weekly --include-facts
```

## yfinance

Fetch a market-data snapshot:

```powershell
python -m stock_research yfinance company --ticker AAPL --run-id 2026-05-09_weekly
```

## FMP

Fetch quote, profile, TTM key metrics, and TTM ratios:

```powershell
python -m stock_research fmp company --ticker AAPL --run-id 2026-05-09_weekly
```

Optional TTM statements:

```powershell
python -m stock_research fmp company --ticker AAPL --run-id 2026-05-09_weekly --include-statements
```

## Polygon / Massive

Fetch U.S. ticker details and previous-day OHLC:

```powershell
python -m stock_research polygon company --ticker AAPL --run-id 2026-05-09_weekly
```

## Alpha Vantage

Fetch Global Quote and Overview:

```powershell
python -m stock_research alpha-vantage company --ticker AAPL --run-id 2026-05-09_weekly
```

Optional statements and earnings:

```powershell
python -m stock_research alpha-vantage company --ticker AAPL --run-id 2026-05-09_weekly --include-statements
```

## Financial Comparison

Compare financial provider packets for one ticker:

```powershell
python -m stock_research financial compare --ticker AAPL --run-id 2026-05-09_weekly
```

This step only compares financial/profile/market-data packets. Exa and xAI/Grok packets are not inputs.

Run the deterministic financial-data specialist review after comparison:

```powershell
python -m stock_research financial review --ticker AAPL --run-id 2026-05-09_weekly
```

## Company News Review

Run Exa contents follow-up for high-value company-news URLs, then review:

```powershell
python -m stock_research news contents-follow-up --ticker AAPL --run-id 2026-05-09_weekly
python -m stock_research news review --ticker AAPL --run-id 2026-05-09_weekly
```

## Exa

Run a news/industry/company search:

```powershell
python -m stock_research exa search --mode news --query "semiconductor supply chain disruptions Europe" --subject-type industry --subject-id semiconductors --run-id 2026-05-09_weekly
```

Extract contents from a URL:

```powershell
python -m stock_research exa contents --url https://example.com/article --subject-type company --subject-id AAPL --run-id 2026-05-09_weekly --highlights-query "investment relevance and risks"
```

## xAI Grok

Research recent X sentiment/news with Grok x_search:

```powershell
python -m stock_research xai x-search --ticker AMD --company-name "Advanced Micro Devices" --subject-type company --subject-id AMD --run-id 2026-05-09_weekly
```

Research an industry/theme:

```powershell
python -m stock_research xai x-search --topic "European grid infrastructure" --research-kind industry_sentiment --subject-type industry --subject-id european_grid_infrastructure --run-id 2026-05-09_weekly
```

## Generated Run Artifacts

Weekly manifests can be written with:

```powershell
python -m stock_research manifest --write
```

The default output path is:

```text
agents/runs/YYYY-MM-DD_weekly/manifest.json
```

Inspect planned provider tasks without making live API calls:

```powershell
python -m stock_research provider-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json
```

Execute planned provider tasks:

```powershell
python -m stock_research provider-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --execute
```

Inspect planned analysis tasks:

```powershell
python -m stock_research analysis-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json
```

Execute planned analysis tasks:

```powershell
python -m stock_research analysis-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --execute
```

Run the deterministic weekly workflow wrapper:

```powershell
python -m stock_research run-weekly
python -m stock_research run-weekly --write
python -m stock_research run-weekly --write --execute-providers --execute-analysis
python -m stock_research run-weekly --write --execute-orchestrator
```

The third command is the default Codex-supervised path. The fourth command is optional API SDK mode.

Apply low-risk factual company-file updates from a completed opportunity-assessment run:

```powershell
python -m stock_research company-file apply-factual-updates --run-id 2026-05-16_weekly --write
python -m stock_research category-state update --run-id 2026-05-16_weekly --write
```

Refresh generated artifact hygiene index:

```powershell
python -m stock_research artifact-hygiene inventory --write
python -m stock_research artifact-hygiene archive
python -m stock_research artifact-hygiene archive --write
```

Write run summary and quality report artifacts:

```powershell
python -m stock_research run-summary --run-id 2026-05-09_weekly --write
python -m stock_research quality-report --run-id 2026-05-09_weekly --write
```

Run markdown artifacts are intended to be inspectable repo state. Generated run JSON files, raw provider JSON, and evidence packet JSON are local runtime artifacts and are ignored by Git.

## Operational Agent Memory

Start with:

```text
agents/memory/memory_index.md
```

The memory files are structured Markdown and require no extra setup. They store operational lessons, source-quality notes, specialist playbooks, evaluation metrics, and deprecated behavior. Do not store secrets, raw provider output, or ordinary company investment facts in `agents/memory/`.

Validate and inspect memory:

```powershell
python -m stock_research memory summary
python -m stock_research memory validate
python -m stock_research memory context --task sentiment
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

Finalize a weekly/manual run after run summary and quality report generation:

```powershell
python -m stock_research memory finalize-run --run-id 2026-05-09_weekly
```

This writes memory reflection artifacts, recurring failure reports, and `finalization.json` / `finalization.md` for the run. It does not apply proposed memory updates automatically.

The bounded memory writer can improve or reject draft memory items before approval, but it does not write to `agents/memory/*.md` directly. Apply approved drafts only through `memory apply-updates`.
