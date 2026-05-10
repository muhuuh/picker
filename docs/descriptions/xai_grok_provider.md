# xAI Grok Provider

Last updated: 2026-05-10

## Purpose

xAI Grok is the provider for X-based social sentiment, latest X news, and community narrative research.

Implementation: `stock_research/providers/xai_grok.py`.

## Official Sources Reviewed

- xAI tools overview: https://docs.x.ai/developers/tools/overview
- xAI X Search tool: https://docs.x.ai/developers/tools/x-search
- xAI citations: https://docs.x.ai/developers/tools/citations

Rechecked on 2026-05-10 before market-discovery specialist work.

## Correct Design

Use `XAI_API_KEY` with Grok and the built-in `x_search` tool.

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

## Current Tool

```powershell
python -m stock_research xai x-search --ticker AMD --company-name "Advanced Micro Devices" --subject-type company --subject-id AMD --run-id 2026-05-09_weekly
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

Official xAI docs currently list these `x_search` parameters: `allowed_x_handles`, `excluded_x_handles`, `from_date`, `to_date`, `enable_image_understanding`, and `enable_video_understanding`. Allowed/excluded handle filters are mutually exclusive and each supports up to 10 handles.

## Weekly Manifest Usage

Weekly manifests should plan `xai_grok` provider tasks by default:

- current holdings and monitoring stocks: Grok `x_search` stock sentiment;
- research priorities: Grok `x_search` industry/theme sentiment;
- human stock/industry/theme requests: routed to Grok `x_search`.

Discovery-specific usage:

- Use a bounded recent date window by default: 14 days for stock/latest-news scans and 21 days for industry/theme discovery.
- Enable image understanding for industry/theme discovery when useful, because X posts often contain charts, screenshots, and product/media context.
- Prompt Grok to surface niche companies, emerging tickers, credible accounts/posts, rumors, hype cycles, skepticism, and verification tasks.
- Treat results as social signal and lead generation only.

Inspect planned xAI tasks:

```powershell
python -m stock_research provider-tasks --manifest agents\runs\2026-05-09_weekly\manifest.json --provider xai_grok
```

## Outputs

Raw xAI JSON:

```text
agents/runs/{run_id}/raw/xai_grok/{artifact_id}.json
```

Evidence packet:

```text
agents/runs/{run_id}/evidence_packets/{packet_id}.json
```

When Grok runs from manifest provider tasks, `artifact_id` is the manifest task id. The provider uses a longer timeout and one retry because live `x_search` responses can be slow.

Live smoke test status:

- 2026-05-03: AMD `x_search` smoke test passed for 2026-05-01 to 2026-05-03.
- Raw artifact: `agents/runs/2026-05-09_weekly/raw/xai_grok/x_search_amd.json`.
- Evidence packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_xai_grok_company_amd.json`.
- 2026-05-04: Manifest-driven AAPL and stock-discovery Grok tasks passed with task-specific artifact names after adding bounded timeout retry behavior.

## Guardrails

- Treat Grok/X output as social sentiment unless independently verified.
- Preserve citations surfaced by Grok as evidence sources.
- Separate investor-relevant facts from community narratives, hype, and speculation.
- Use Exa/SEC/yfinance/FMP/Polygon/Alpha Vantage to verify material factual claims.
