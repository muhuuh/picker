# FMP Provider

Last updated: 2026-05-04

## Purpose

Financial Modeling Prep is used as a market-data and fundamentals cross-check provider.

Implementation: `stock_research/providers/fmp.py`.

## Official Sources Reviewed

- FMP quickstart: https://site.financialmodelingprep.com/developer/docs/quickstart
- FMP stable API docs: https://site.financialmodelingprep.com/developer/docs/stable
- FMP key metrics TTM docs: https://site.financialmodelingprep.com/developer/docs/stable/key-metrics-ttm
- FMP ratios TTM docs: https://site.financialmodelingprep.com/developer/docs/stable/metrics-ratios-ttm

## Current Tool

```powershell
python -m stock_research fmp company --ticker AAPL --run-id 2026-05-09_weekly
```

Optional heavier pull:

```powershell
python -m stock_research fmp company --ticker AAPL --run-id 2026-05-09_weekly --include-statements
```

## Data Pulled

Default:

- `quote`
- `profile`
- `key-metrics-ttm`
- `ratios-ttm`

With `--include-statements`:

- `income-statement-ttm`
- `balance-sheet-statement-ttm`
- `cash-flow-statement-ttm`

## Configuration

```text
FMP_API_KEY="..."
```

`FINANCIAL_MODELING_PREP_API_KEY` is also accepted.

## Workflow Role

FMP should be used in deterministic kickoff for current holdings, monitoring stocks, and human stock-research requests. It should also be callable by future financial-data specialists.

Use it to cross-check yfinance and to add TTM valuation/fundamental ratios before the orchestrator draws investment conclusions.

## Live Smoke Test

- 2026-05-04: AAPL live smoke test passed.
- Evidence packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_fmp_company_aapl.json`.
- Raw artifact: `agents/runs/2026-05-09_weekly/raw/fmp/AAPL_snapshot.json`.
