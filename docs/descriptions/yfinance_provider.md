# yfinance Provider

Last updated: 2026-05-24

## Purpose

yfinance provides quick market-data snapshots for monitored stocks and current holdings.

Implementation: `stock_research/providers/yfinance_provider.py`.

## Source Notes

- yfinance is an open-source wrapper around Yahoo Finance data.
- It is useful for quick research snapshots.
- It should not be the only source of truth for high-impact decisions.
- Later market-data tools should cross-check key metrics with FMP, Polygon, Alpha Vantage, or another paid provider.

## Dependency

```powershell
python -m pip install yfinance
```

The repo declares:

```text
yfinance>=1.2.2
```

## CLI

Fetch a company market-data snapshot:

```powershell
python -m stock_research yfinance company --ticker AAPL --run-id 2026-05-09_weekly
```

Use another history window:

```powershell
python -m stock_research yfinance company --ticker AAPL --period 1mo --run-id 2026-05-09_weekly
```

## Outputs

Raw yfinance JSON:

```text
agents/runs/{run_id}/raw/yfinance/{TICKER}_snapshot.json
```

Evidence packet:

```text
agents/runs/{run_id}/evidence_packets/{packet_id}.json
```

## Current Metrics

The evidence packet attempts to extract:

- company name,
- country,
- currency,
- last price,
- previous close,
- market cap,
- P/E ratio,
- forward P/E,
- PEG ratio,
- price-to-sales TTM,
- price-to-book ratio,
- EV/EBITDA TTM,
- revenue TTM,
- EPS,
- profit margin,
- debt/equity,
- 52-week low/high,
- exchange,
- sector,
- industry.

Missing metrics are recorded as `unknowns`.

## Validation

- 2026-05-03: Live yfinance smoke test passed for AAPL.
- Output packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-03_yfinance_company_aapl.json`.
- Raw snapshot: `agents/runs/2026-05-09_weekly/raw/yfinance/AAPL_snapshot.json`.
- 2026-05-24: Extended valuation/profile metric extraction was added after the Soitec `SOI.PA` Sheet correction showed raw yfinance data contained P/S and forward P/E fields that were not previously exposed to `financial_compare`.
