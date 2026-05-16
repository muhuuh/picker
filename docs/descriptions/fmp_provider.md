# FMP Provider

Last updated: 2026-05-16

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
FMP_API_KEY2="..." # optional fallback
```

`FINANCIAL_MODELING_PREP_API_KEY` is also accepted.

The provider tries `FMP_API_KEY` first. If FMP returns a tier/subscription, rate-limit, or credential-style failure, the workflow retries once with `FMP_API_KEY2` when configured. Secret values are never written to run artifacts; raw artifacts record only `primary`/`secondary` labels and sanitized error messages. If both keys fail, the provider still writes an explicit unavailable evidence packet so weekly runs continue with other financial providers.

Endpoint behavior is also partial-success aware. Some smaller or OTC tickers can return usable `profile` data while `quote` or TTM endpoints return FMP 402 plan/ticker-coverage responses. In that case the packet is still written as a medium-confidence FMP snapshot with endpoint-level unknowns instead of discarding the usable profile data. When a fallback key is configured, blocked endpoints are retried against the secondary key before the endpoint-level unknowns are finalized.

## Workflow Role

FMP should be used in deterministic kickoff for current holdings, monitoring stocks, and human stock-research requests. It should also be callable by future financial-data specialists.

Use it to cross-check yfinance and to add TTM valuation/fundamental ratios before the orchestrator draws investment conclusions.

## Live Smoke Test

- 2026-05-04: AAPL live smoke test passed.
- Evidence packet: `agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_fmp_company_aapl.json`.
- Raw artifact: `agents/runs/2026-05-09_weekly/raw/fmp/AAPL_snapshot.json`.
- 2026-05-16: Official endpoint shape rechecked against FMP stable docs. Both configured keys worked for AAPL/GOOGL. AXTI/KRKNF returned FMP 402 on quote/TTM endpoints but returned profile data, which is now preserved as partial FMP evidence.
