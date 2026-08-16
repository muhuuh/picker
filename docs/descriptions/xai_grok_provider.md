# xAI Grok Provider

Last updated: 2026-08-16

## Purpose

xAI Grok is the provider for X-based social sentiment, latest X news, community narrative research, and auxiliary web deep-dive context.

Implementation: `stock_research/providers/xai_grok.py`.

## Official Sources Reviewed

- xAI tools overview: https://docs.x.ai/developers/tools/overview
- xAI Web Search tool: https://docs.x.ai/developers/tools/web-search
- xAI X Search tool: https://docs.x.ai/developers/tools/x-search
- xAI citations: https://docs.x.ai/developers/tools/citations
- xAI Grok 4.6: https://docs.x.ai/developers/grok-4-6
- xAI model-list endpoint: https://docs.x.ai/developers/rest-api-reference/inference/models
- xAI reasoning controls: https://docs.x.ai/developers/model-capabilities/text/reasoning

Rechecked on 2026-08-16 for the Grok 4.6 migration and authenticated model resolution.

## Correct Design

Use `XAI_API_KEY` with Grok and the built-in `x_search` tool for X-native work.

Use Grok `web_search` for auxiliary company deep dives only when the workflow has identified a current business, news, analyst-context, or verification gap.

Do not use the direct X.com / Twitter API v2 recent search/counts endpoints for this repo.

Reason:

- Grok has built-in X search that can perform keyword search, semantic search, user search, and thread fetch on X.
- Grok can analyze posts and summarize sentiment/news in one step.
- The Responses API returns citations, including X post URLs, which are better suited for our evidence packet workflow.
- This avoids maintaining direct X API search/count logic and keeps social research in the specialist-agent model.

## Configuration

```text
XAI_API_KEY="..."
```

No `X_BEARER_TOKEN` is needed for this design.

The configured search model is `grok-4.6`. Before a live provider task executes, the provider reads `/v1/models` with the same API key, resolves the requested model, and fails clearly when neither the requested model nor an approved X-search fallback is available. It never replaces an unavailable X-search lane with generic web search.

Inspect the account-visible model catalog without running research:

```powershell
python -m stock_research xai models --requested-model grok-4.6
```

The 2026-08-16 authenticated check confirmed that the configured account exposes `grok-4.6` directly.

## Current Tool

X sentiment:

```powershell
python -m stock_research xai x-search --ticker AMD --company-name "Advanced Micro Devices" --subject-type company --subject-id AMD --run-id 2026-05-09_weekly
```

Company web deep dive:

```powershell
python -m stock_research xai web-search --ticker AMBA --company-name "Ambarella" --subject-type company --subject-id AMBA --run-id 2026-05-17_manual-xai
```

Industry/theme sentiment:

```powershell
python -m stock_research xai x-search --topic "European grid infrastructure" --research-kind industry_sentiment --subject-type industry --subject-id european_grid_infrastructure --run-id 2026-05-09_weekly
```

Latest X news:

```powershell
python -m stock_research xai x-search --topic "ASML export controls" --research-kind latest_news --subject-type company --subject-id ASML --run-id 2026-05-09_weekly
```

Useful options:

- `--from-date YYYY-MM-DD`
- `--to-date YYYY-MM-DD`
- `--allowed-x-handle HANDLE`
- `--excluded-x-handle HANDLE`
- `--enable-image-understanding`
- `--enable-video-understanding`
- `--reasoning-effort low|medium|high|xhigh` (default: `high`)

Official xAI docs currently list these `x_search` parameters: `allowed_x_handles`, `excluded_x_handles`, `from_date`, `to_date`, `enable_image_understanding`, and `enable_video_understanding`. Allowed/excluded handle filters are mutually exclusive and each supports up to 20 handles.

Official xAI docs currently list these `web_search` parameters: `allowed_domains`, `excluded_domains`, and `enable_image_understanding`. Allowed/excluded domain filters are mutually exclusive and each supports up to 5 domains. xAI docs state Web Search runs on the Responses API and can search/browse current web pages.

## Weekly Manifest Usage

Weekly manifests should plan `xai_grok` provider tasks by default:

- current holdings and monitoring stocks: Grok `x_search` stock sentiment;
- each deduplicated portfolio-industry cluster: one shared Grok 4.6 `x_search` industry pulse;
- research priorities: Grok `x_search` industry/theme sentiment;
- human stock/industry/theme requests: routed to Grok `x_search`.

Per-ticker Grok `web_search` plans are stored under `deferred_provider_tasks` with `execution_policy: gap_triggered`. The normal provider runner executes only `provider_tasks`, so these web deep dives do not run unless a later gap-detection step explicitly promotes them. This preserves Grok's X-native advantage and avoids duplicating Exa/company/financial research.

Discovery-specific usage:

- Use a bounded recent date window by default: 14 days for stock/latest-news scans and 21 days for industry/theme discovery.
- Enable image understanding for industry/theme discovery when useful, because X posts often contain charts, screenshots, and product/media context.
- Prompt Grok to surface niche companies, emerging tickers, credible accounts/posts, rumors, hype cycles, skepticism, and verification tasks.
- Company and industry prompts must ask for investor-grade sections, not just a sentiment label: X/community pulse, trend evolution, verified facts, bull narratives, bear/skeptical narratives, non-obvious angles, notable accounts/posts, hype/noise/rumors, candidate follow-up, and an investor scorecard.
- Treat results as social signal and lead generation only.
- Treat `web_search` results as auxiliary context, not a source of truth. Use them to spot missing business/industry/news/analyst details, then verify material claims through Exa contents, filings, company sources, and financial providers.

Inspect planned xAI tasks:

```powershell
python -m stock_research provider-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --provider xai_grok
```

## Outputs

Raw xAI JSON:

```text
agents/runs/{run_id}/raw/xai_grok/{artifact_id}.json
```

Every raw artifact includes `model_provenance` with:

- requested model;
- resolved model;
- tool type;
- reasoning effort;
- resolution source;
- fallback reason, when used.

Evidence packet:

```text
agents/runs/{run_id}/evidence_packets/{packet_id}.json
```

When Grok runs from manifest provider tasks, `artifact_id` is the manifest task id. The provider uses a longer timeout and one retry because live `x_search` responses can be slow.

Long run ids, subject ids, and manifest task ids are compacted with a stable hash in packet filenames so Windows path length does not break evidence packet writes.

The canonical Grok claim preserves the complete extracted response text. Its `display_excerpt` is only a bounded complete-sentence navigation view; `full_evidence_path` and `full_evidence_selector` point to the raw response. Agent tools load bounded packet summaries first and retrieve one selected full claim on demand, so context limits do not destroy X pulse, bull/bear narratives, candidate follow-up, scorecards, or auxiliary web sections.

Live smoke test status:

- 2026-05-03: AMD `x_search` smoke test passed for 2026-05-01 to 2026-05-03.
- Raw artifact: `agents/runs/2026-05-09_weekly/raw/xai_grok/x_search_amd.json`.
- Evidence packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_xai_grok_company_amd.json`.
- 2026-05-04: Manifest-driven AAPL and stock-discovery Grok tasks passed with task-specific artifact names after adding bounded timeout retry behavior.
- 2026-08-16: Authenticated `/v1/models` resolution returned `grok-4.6` with no fallback. Bounded Grok 4.6 `x_search` smokes passed for GOOGL and the AI semiconductor supply chain, producing 45 and 4 X citation sources respectively with provenance recorded under `agents/runs/2026-08-16_grok-46-smoke/`.

## Guardrails

- Treat Grok/X output as social sentiment unless independently verified.
- Preserve citations surfaced by Grok as evidence sources.
- Separate investor-relevant facts from community narratives, hype, and speculation.
- Use Exa/SEC/yfinance/FMP/Polygon/Alpha Vantage to verify material factual claims.
- Do not promote Grok-only leads, or rumor-like leads, directly to monitoring. Route them through candidate review and follow-up verification first.
