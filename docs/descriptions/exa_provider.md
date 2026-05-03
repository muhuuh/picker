# Exa Provider

Last updated: 2026-05-03

## Purpose

Exa is the main web, news, company-discovery, and content-extraction provider for the research workflow.

Implementation: `stock_research/providers/exa.py`.

## Official Sources Reviewed

- Search API guide: https://exa.ai/docs/reference/search-api-guide-for-coding-agents
- Search best practices: https://exa.ai/docs/reference/search-best-practices
- Company vertical: https://exa.ai/docs/reference/verticals/company-for-coding-agents
- News vertical: https://exa.ai/docs/reference/verticals/news-for-coding-agents
- Contents API guide: https://exa.ai/docs/reference/contents-api-guide-for-coding-agents
- Contents best practices: https://exa.ai/docs/reference/contents-best-practices

## Configuration

Exa requires an API key:

```text
EXA_API_KEY="..."
```

Keep the key in `.env` or a local environment variable. Do not commit `.env`.

## Current Design Decision

Build Exa as deterministic provider tools first, then wrap those tools with specialist agents later.

Reason:

- Provider tools are testable without LLM behavior.
- Raw responses and evidence packets are auditable.
- Specialists can later call the same Exa tools for company news, industry research, market discovery, and content extraction.
- The orchestrator can compare Exa packets with SEC, yfinance, FMP, Polygon, Alpha Vantage, and X.com packets.

## Exa Best Practices Applied

- Use `POST https://api.exa.ai/search` and `POST https://api.exa.ai/contents` directly with raw JSON.
- Use `x-api-key` authentication.
- Send explicit `User-Agent` and `Accept: application/json` headers. Live smoke testing hit HTTP 403 code 1010 without them.
- Use `contents.highlights: true` for search by default because highlights are token-efficient for agent workflows.
- Keep search content parameters nested under `contents`.
- Keep contents endpoint extraction parameters top-level, not nested under `contents`.
- Use `type: "auto"` by default.
- Use `deep`, `deep-lite`, or `deep-reasoning` only when a specialist needs multi-step synthesis or structured output.
- Use `maxAgeHours` only when freshness requirements justify slower live crawling.
- Do not use deprecated parameters like `useAutoprompt`, `numSentences`, `highlightsPerUrl`, `tokensNum`, or `livecrawl`.
- Do not use URL-level include/exclude filters; use domain filters.
- For company search, use `category: "company"` and do not use date filters or `excludeDomains`.
- For news, use specific natural-language queries, optional date filters, optional source-domain filters, and highlights.
- For contents, check `statuses` because individual URL failures can be returned inside a successful HTTP response.

## CLI

Company discovery:

```powershell
python -m stock_research exa search --mode company --query "German robotics suppliers with public-market relevance" --subject-type industry --subject-id robotics --run-id 2026-05-09_weekly
```

Industry or theme news:

```powershell
python -m stock_research exa search --mode news --query "semiconductor supply chain disruptions Europe" --subject-type industry --subject-id semiconductors --run-id 2026-05-09_weekly --start-published-date 2026-04-01
```

Deep page extraction:

```powershell
python -m stock_research exa contents --url https://example.com/article --subject-type company --subject-id AAPL --run-id 2026-05-09_weekly --highlights-query "investment relevance and risks"
```

## Outputs

Raw Exa JSON:

```text
agents/runs/{run_id}/raw/exa/search_{subject_id}.json
agents/runs/{run_id}/raw/exa/contents_{subject_id}.json
```

Evidence packet:

```text
agents/runs/{run_id}/evidence_packets/{packet_id}.json
```

## Validation

- 2026-05-03: Live Exa search smoke test passed for semiconductor industry news.
- Search packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_exa_industry_semiconductors.json`.
- Raw search response: `agents/runs/2026-05-09_weekly/raw/exa/search_semiconductors.json`.
- 2026-05-03: Live Exa contents smoke test passed for SEC EDGAR docs.
- Contents packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_exa_theme_sec_edgar_docs.json`.
- Raw contents response: `agents/runs/2026-05-09_weekly/raw/exa/contents_sec_edgar_docs.json`.

## Current Limits

- Current tool writes search result highlights and contents excerpts into evidence packets.
- It does not yet use Exa `outputSchema`; this should be added when the specialist-agent layer needs structured synthesis.
- Live smoke tests were small and only validate connectivity/basic packet creation, not full search quality.
