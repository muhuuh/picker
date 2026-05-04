# Polygon / Massive Provider

Last updated: 2026-05-04

## Purpose

Polygon/Massive is used as a U.S. stock market-data cross-check provider.

Implementation: `stock_research/providers/polygon_provider.py`.

## Official Sources Reviewed

- Massive/Polygon REST quickstart: https://massive.com/docs/rest/quickstart
- Ticker overview: https://massive.com/docs/rest/stocks/tickers/ticker-overview
- Previous-day OHLC bar: https://massive.com/docs/rest/stocks/aggregates/previous-day-bar
- Changelog and financials status: https://www.massive.com/changelog

## Current Tool

```powershell
python -m stock_research polygon company --ticker AAPL --run-id 2026-05-09_weekly
```

Unadjusted previous-day bar:

```powershell
python -m stock_research polygon company --ticker AAPL --run-id 2026-05-09_weekly --unadjusted
```

## Data Pulled

- Ticker details: `v3/reference/tickers/{ticker}`
- Previous-day OHLC: `v2/aggs/ticker/{ticker}/prev`

## Configuration

```text
POLYGON_API_KEY="..."
```

`MASSIVE_API_KEY` is also accepted. Massive is the current dashboard/docs brand for the API formerly known mainly as Polygon in many integrations.

## Workflow Role

Polygon/Massive should be planned by default for U.S. tracked tickers. Do not assume it covers European equities in the same way.

Use it to verify U.S. ticker identity, exchange, market cap, and previous-day OHLCV.

Current note: Polygon has moved branding/docs toward Massive. The repo keeps the provider name `polygon` because that is how the user and many integrations still refer to it.

## Live Smoke Test

- 2026-05-04: AAPL live smoke test passed.
- Evidence packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_polygon_company_aapl.json`.
- Raw artifact: `agents/runs/2026-05-09_weekly/raw/polygon/AAPL_snapshot.json`.
